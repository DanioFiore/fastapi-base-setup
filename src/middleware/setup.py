"""
Middleware setup module for FastAPI application.

This module provides functions to configure and add middleware to a FastAPI app,
including CORS, logging, and rate limiting. It supports different configurations
for development and production environments.

Functions:
    - setup_middleware(app: FastAPI) -> None:
        Sets up CORS, logging, and rate limiting middleware. Attempts to connect
        to Redis for rate limiting; disables rate limiting if Redis is unavailable.

    - setup_development_middleware(app: FastAPI) -> None:
        Configures middleware for development with permissive CORS and logging.
        Rate limiting is disabled or uses an in-memory limiter.

    - setup_production_middleware(app: FastAPI) -> None:
        Configures middleware for production with strict CORS, logging, and
        Redis-based rate limiting.

Dependencies:
    - fastapi.FastAPI
    - redis.Redis
    - core.config.settings
    - middleware.cors
    - middleware.logging
    - middleware.rate_limiting

"""
import redis
from fastapi import FastAPI
from redis.exceptions import RedisError
from core.config import settings
from middleware.cors import configure_cors_for_development
from middleware.cors import add_cors_middleware
from middleware.logging import add_logging_middleware
from middleware.rate_limiting import add_rate_limiting_middleware
from middleware.cors import configure_cors_for_production


def setup_middleware(app: FastAPI) -> None:
    """
    Setup all middleware for the FastAPI application.

    This function configures:
    - CORS middleware for cross-origin requests
    - Logging middleware for request/response logging
    - Rate limiting middleware for API protection

    Args:
        app: The FastAPI application instance
    """

    # 1. Add CORS middleware (should be added first)
    add_cors_middleware(app)

    # 2. Add logging middleware
    add_logging_middleware(app)

    # 3. Add rate limiting middleware (should be added last)
    redis_client = None
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
        # Test connection
        redis_client.ping()
        print("✅ Redis connection successful - Rate limiting enabled")
    except RedisError as e:
        print(f"⚠️  Redis connection failed: {e} - Rate limiting will be disabled")
        redis_client = None

    add_rate_limiting_middleware(app, redis_client)


def setup_development_middleware(app: FastAPI) -> None:
    """
    Setup middleware for development environment with more permissive settings.

    Args:
        app: The FastAPI application instance
    """

    # More permissive CORS for development
    configure_cors_for_development(app)

    # Add logging middleware
    add_logging_middleware(app)

    # Skip rate limiting in development or use in-memory limiter
    print("🔧 Development mode - Rate limiting disabled")


def setup_production_middleware(app: FastAPI) -> None:
    """
    Setup middleware for production environment with strict settings.

    Args:
        app: The FastAPI application instance
    """
    # Strict CORS for production
    configure_cors_for_production(app)

    # Add logging middleware
    add_logging_middleware(app)

    # Redis-based rate limiting for production
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        decode_responses=True,
    )

    add_rate_limiting_middleware(app, redis_client)
    print("🔒 Production mode - All security middleware enabled")
