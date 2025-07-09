"""
Rate Limiting Middleware for FastAPI
"""
import time
from typing import Callable, Optional

import redis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from redis.exceptions import RedisError

from core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis for distributed rate limiting.

    This middleware implements:
    - Token bucket algorithm for rate limiting
    - Per-IP and per-user rate limiting
    - Different limits for different endpoints
    - Configurable time windows
    """

    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.redis_client: Optional[redis.Redis] = (
            redis_client or self._create_redis_client()
        )
        self.default_requests_per_minute = settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        self.default_requests_per_hour = settings.RATE_LIMIT_REQUESTS_PER_HOUR

        # Define endpoint-specific rate limits
        self.endpoint_limits = {
            "/api/auth/login": {"requests_per_minute": 5, "requests_per_hour": 20},
            "/api/auth/register": {"requests_per_minute": 3, "requests_per_hour": 10},
            "/api/auth/forgot-password": {
                "requests_per_minute": 2,
                "requests_per_hour": 5,
            },
            "/api/users/": {"requests_per_minute": 30, "requests_per_hour": 1000},
        }

    def _create_redis_client(self) -> Optional[redis.Redis]:
        """
        Create Redis client for rate limiting.

        Returns:
            Redis client instance or None if connection fails
        """
        try:
            client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
            )
            # Test connection
            client.ping()
            return client
        except RedisError as e:
            print(
                f"Warning: Redis connection failed: {e}. Rate limiting will be disabled."
            )
            return None

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request with rate limiting.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response or rate limit error
        """
        # Skip rate limiting if Redis is not available
        if not self.redis_client:
            return await call_next(request)

        # Skip rate limiting for health checks and static files
        if self._should_skip_rate_limiting(request):
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_identifier(request)

        # Get rate limits for this endpoint
        limits = self._get_endpoint_limits(request.url.path)

        # Check rate limits
        rate_limit_result = self._check_rate_limits(
            client_id, request.url.path, limits
        )

        if not rate_limit_result["allowed"]:
            return self._create_rate_limit_response(rate_limit_result)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        self._add_rate_limit_headers(response, rate_limit_result)

        return response

    def _should_skip_rate_limiting(self, request: Request) -> bool:
        """
        Determine if rate limiting should be skipped for this request.

        Args:
            request: The incoming request

        Returns:
            True if rate limiting should be skipped
        """
        skip_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
        ]

        return any(request.url.path.startswith(path) for path in skip_paths)

    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for the client.

        Args:
            request: The incoming request

        Returns:
            Client identifier string
        """
        # Try to get user ID from request state (if authenticated)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"

        # Consider X-Forwarded-For header for proxy setups
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        return f"ip:{client_ip}"

    def _get_endpoint_limits(self, path: str) -> dict:
        """
        Get rate limits for a specific endpoint.

        Args:
            path: The request path

        Returns:
            Dictionary with rate limits
        """
        # Check for exact match
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]

        # Check for prefix match
        for endpoint_path, limits in self.endpoint_limits.items():
            if path.startswith(endpoint_path):
                return limits

        # Return default limits
        return {
            "requests_per_minute": self.default_requests_per_minute,
            "requests_per_hour": self.default_requests_per_hour,
        }

    def _check_rate_limits(self, client_id: str, path: str, limits: dict) -> dict:
        """
        Check if client has exceeded rate limits.

        Args:
            client_id: Client identifier
            path: Request path
            limits: Rate limits to check

        Returns:
            Dictionary with rate limit check results
        """
        current_time = int(time.time())

        # Check minute-based limit
        minute_key = f"rate_limit:{client_id}:{path}:minute:{current_time // 60}"
        minute_count = self._increment_counter(minute_key, 60)

        # Check hour-based limit
        hour_key = f"rate_limit:{client_id}:{path}:hour:{current_time // 3600}"
        hour_count = self._increment_counter(hour_key, 3600)

        # Determine if request is allowed
        minute_exceeded = minute_count > limits["requests_per_minute"]
        hour_exceeded = hour_count > limits["requests_per_hour"]

        allowed = not (minute_exceeded or hour_exceeded)

        return {
            "allowed": allowed,
            "minute_count": minute_count,
            "minute_limit": limits["requests_per_minute"],
            "hour_count": hour_count,
            "hour_limit": limits["requests_per_hour"],
            "reset_time_minute": (current_time // 60 + 1) * 60,
            "reset_time_hour": (current_time // 3600 + 1) * 3600,
        }

    def _increment_counter(self, key: str, ttl: int) -> int:
        """
        Increment Redis counter with TTL.

        Args:
            key: Redis key
            ttl: Time to live in seconds

        Returns:
            Current counter value
        """
        try:
            if not self.redis_client:
                return 0
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl)
            results = pipe.execute()
            return results[0]
        except RedisError as e:
            print(f"Redis error: {e}")
            return 0

    def _create_rate_limit_response(self, rate_limit_result: dict) -> JSONResponse:
        """
        Create rate limit exceeded response.

        Args:
            rate_limit_result: Rate limit check results

        Returns:
            JSON response with rate limit error
        """
        current_time = int(time.time())

        # Calculate retry after time
        retry_after_minute = rate_limit_result["reset_time_minute"] - current_time
        retry_after_hour = rate_limit_result["reset_time_hour"] - current_time
        retry_after = min(retry_after_minute, retry_after_hour)

        headers = {
            "X-RateLimit-Limit-Minute": str(rate_limit_result["minute_limit"]),
            "X-RateLimit-Remaining-Minute": str(
                max(
                    0,
                    rate_limit_result["minute_limit"]
                    - rate_limit_result["minute_count"],
                )
            ),
            "X-RateLimit-Reset-Minute": str(rate_limit_result["reset_time_minute"]),
            "X-RateLimit-Limit-Hour": str(rate_limit_result["hour_limit"]),
            "X-RateLimit-Remaining-Hour": str(
                max(
                    0, rate_limit_result["hour_limit"] - rate_limit_result["hour_count"]
                )
            ),
            "X-RateLimit-Reset-Hour": str(rate_limit_result["reset_time_hour"]),
            "Retry-After": str(retry_after),
        }

        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": retry_after,
            },
            headers=headers,
        )

    def _add_rate_limit_headers(self, response, rate_limit_result: dict) -> None:
        """
        Add rate limit headers to successful response.

        Args:
            response: The response object
            rate_limit_result: Rate limit check results
        """
        response.headers["X-RateLimit-Limit-Minute"] = str(
            rate_limit_result["minute_limit"]
        )
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            max(
                0, rate_limit_result["minute_limit"] - rate_limit_result["minute_count"]
            )
        )
        response.headers["X-RateLimit-Reset-Minute"] = str(
            rate_limit_result["reset_time_minute"]
        )
        response.headers["X-RateLimit-Limit-Hour"] = str(
            rate_limit_result["hour_limit"]
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            max(0, rate_limit_result["hour_limit"] - rate_limit_result["hour_count"])
        )
        response.headers["X-RateLimit-Reset-Hour"] = str(
            rate_limit_result["reset_time_hour"]
        )


def add_rate_limiting_middleware(
    app: FastAPI, redis_client: Optional[redis.Redis] = None
) -> None:
    """
    Add rate limiting middleware to the FastAPI application.

    Args:
        app: The FastAPI application instance
        redis_client: Optional Redis client instance
    """
    app.add_middleware(RateLimitMiddleware, redis_client=redis_client)


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter for development/testing.
    Not recommended for production use.
    """

    def __init__(self):
        self.requests = {}

    def is_allowed(self, client_id: str, limit: int, window: int) -> bool:
        """
        Check if request is allowed based on in-memory counters.

        Args:
            client_id: Client identifier
            limit: Request limit
            window: Time window in seconds

        Returns:
            True if request is allowed
        """
        current_time = time.time()
        window_start = current_time - window

        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time
                for req_time in self.requests[client_id]
                if req_time > window_start
            ]
        else:
            self.requests[client_id] = []

        # Check if limit exceeded
        if len(self.requests[client_id]) >= limit:
            return False

        # Add current request
        self.requests[client_id].append(current_time)
        return True
