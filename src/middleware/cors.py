from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings


def add_cors_middleware(app: FastAPI) -> None:
    """
    Add CORS middleware to the FastAPI application.
    
    This middleware handles Cross-Origin Resource Sharing (CORS) to allow
    web applications running at different origins to access the API.
    
    Args:
        app: The FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        expose_headers=settings.CORS_EXPOSE_HEADERS,
        max_age=settings.CORS_MAX_AGE,
    )


def configure_cors_for_development(app: FastAPI) -> None:
    """
    Configure CORS for development environment with more permissive settings.
    
    Args:
        app: The FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins in development
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )


def configure_cors_for_production(app: FastAPI) -> None:
    """
    Configure CORS for production environment with strict settings.
    
    Args:
        app: The FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://yourdomain.com",
            "https://www.yourdomain.com",
            "https://app.yourdomain.com",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
        ],
        expose_headers=["X-Total-Count", "X-Page-Count"],
        max_age=86400,  # 24 hours
    )