import time
import logging
import uuid
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from core.config import settings


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log") if settings.LOG_TO_FILE else logging.NullHandler(),
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
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request {request_id} failed: {str(e)} | "
                f"Method: {request.method} | "
                f"URL: {request.url} | "
                f"Process time: {process_time:.4f}s"
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id},
                headers={"X-Request-ID": request_id, "X-Process-Time": str(process_time)},
            )

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
            f"Request {request_id} started | "
            f"Method: {request.method} | "
            f"URL: {request.url} | "
            f"Client IP: {client_ip} | "
            f"User Agent: {user_agent}"
        )
        
        # Log headers in debug mode
        if settings.LOG_LEVEL.upper() == "DEBUG":
            headers = dict(request.headers)
            # Remove sensitive headers
            headers.pop("authorization", None)
            headers.pop("cookie", None)
            logger.debug(f"Request {request_id} headers: {headers}")
            
            # Log request body for POST/PUT/PATCH requests
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body:
                        # Limit body size in logs
                        body_str = body.decode("utf-8")[:1000]
                        logger.debug(f"Request {request_id} body: {body_str}")
                except Exception as e:
                    logger.debug(f"Request {request_id} body read error: {str(e)}")

    def _log_response(self, request: Request, response: Response, process_time: float, request_id: str) -> None:
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
            f"Request {request_id} completed | "
            f"Method: {request.method} | "
            f"URL: {request.url} | "
            f"Status: {response.status_code} | "
            f"Process time: {process_time:.4f}s"
        )
        
        # Log response headers in debug mode
        if settings.LOG_LEVEL.upper() == "DEBUG":
            headers = dict(response.headers)
            logger.debug(f"Response {request_id} headers: {headers}")


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


def log_user_action(request: Request, action: str, details: dict = None) -> None:
    """
    Log user actions for audit purposes.
    
    Args:
        request: The current request
        action: Description of the action
        details: Additional details about the action
    """
    request_id = getattr(request.state, "request_id", "unknown")
    user_id = getattr(request.state, "user_id", "anonymous")
    
    log_data = {
        "request_id": request_id,
        "user_id": user_id,
        "action": action,
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
    }
    
    if details:
        log_data.update(details)
    
    logger.info(f"User action: {log_data}")