"""
Logging middleware for FastAPI applications.

This module provides a `LoggingMiddleware` class that logs HTTP request and response details,
including method, URL, headers, body, status code, processing time, 
and a unique request ID for tracing.
It also includes utility functions to add the middleware to a FastAPI app, 
obtain a logger with request context,
and log user actions for audit purposes.

Classes:
    LoggingMiddleware: Middleware for logging HTTP requests and responses.

Functions:
    add_logging_middleware(app: FastAPI) -> None:
        Adds the logging middleware to the FastAPI application.

    get_request_logger(request: Request) -> logging.Logger:
        Returns a logger instance with request ID context for the current request.

    log_user_action(request: Request, action: str, details: Optional[Dict] = None) -> None:
        Logs user actions for audit purposes, including request and user information.

Configuration:
    Logging is configured based on settings from `core.config.settings`, 
    supporting log level and file logging.
    Each request is assigned a unique request ID, 
    which is included in logs and response headers for traceability.
"""
import logging
import time
import uuid
from typing import Callable, Dict, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, str(settings.LOG_LEVEL).upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        (
            logging.FileHandler("app.log")
            if settings.LOG_TO_FILE
            else logging.NullHandler()
        ),
    ],
)

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.

    This middleware logs:
    - Request details (method, URL, headers, body)
    - Response details (status code, headers)
    - Request processing time
    - Unique request ID for tracing
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Start timing
        start_time = time.time()

        # Log request
        await self._log_request(request, request_id)

        # Add request ID to request state
        request.state.request_id = request_id

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            # Log response
            self._log_response(request, response, process_time, request_id)

            return response
        except Exception as e:
            # Catching general exception is discouraged; handle known exceptions or re-raise
            process_time = time.time() - start_time
            logger.error(
                "Request %s failed: %s | Method: %s | URL: %s | Process time: %.4fs",
                request_id,
                str(e),
                request.method,
                request.url,
                process_time,
            )
            # Optionally, re-raise if you want to propagate unknown exceptions
            raise

    async def _log_request(self, request: Request, request_id: str) -> None:
        """
        Log incoming request details.

        Args:
            request: The incoming request
            request_id: Unique request identifier
        """
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Get user agent
        user_agent = request.headers.get("user-agent", "unknown")

        # Log basic request info
        logger.info(
            "Request %s started | Method: %s | URL: %s | Client IP: %s | User Agent: %s",
            request_id,
            request.method,
            request.url,
            client_ip,
            user_agent,
        )

        # Log headers in debug mode
        if str(settings.LOG_LEVEL).upper() == "DEBUG":
            headers = dict(request.headers)
            # Remove sensitive headers
            headers.pop("authorization", None)
            headers.pop("cookie", None)
            logger.debug("Request %s headers: %s", request_id, headers)

            # Log request body for POST/PUT/PATCH requests
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body:
                        body_str = body.decode("utf-8")[:1000]
                        logger.debug("Request %s body: %s", request_id, body_str)
                except (UnicodeDecodeError, RuntimeError) as e:
                    # Reading body can fail for these reasons
                    logger.debug("Request %s body read error: %s", request_id, str(e))

    def _log_response(
        self, request: Request, response: Response, process_time: float, request_id: str
    ) -> None:
        """
        Log response details.

        Args:
            request: The original request
            response: The response
            process_time: Time taken to process the request
            request_id: Unique request identifier
        """
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO

        logger.log(
            log_level,
            "Request %s completed | Method: %s | URL: %s | Status: %d | Process time: %.4fs",
            request_id,
            request.method,
            request.url,
            response.status_code,
            process_time,
        )

        # Log response headers in debug mode
        if str(settings.LOG_LEVEL).upper() == "DEBUG":
            headers = dict(response.headers)
            logger.debug("Response %s headers: %s", request_id, headers)


def add_logging_middleware(app: FastAPI) -> None:
    """
    Add logging middleware to the FastAPI application.

    Args:
        app: The FastAPI application instance
    """
    app.add_middleware(LoggingMiddleware)


def get_request_logger(request: Request) -> logging.Logger:
    """
    Get a logger with request context.

    Args:
        request: The current request

    Returns:
        Logger instance with request ID context
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger_with_context = logging.getLogger(f"{__name__}.{request_id}")
    return logger_with_context


def log_user_action(
    request: Request, action: str, details: Optional[Dict] = None
) -> None:
    """
    Log user actions for audit purposes.

    Args:
        request: The current request
        action: Description of the action
        details: Additional details about the action
    """
    if details is None:
        details = {}
    request_id = getattr(request.state, "request_id", "unknown")
    user_id = getattr(request.state, "user_id", "anonymous")
    log_data = {
        "request_id": request_id,
        "user_id": user_id,
        "action": action,
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
    }
    log_data.update(details)
    logger.info("User action: %s", log_data)
