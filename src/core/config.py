from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import Optional, List, Union
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Settings
    APP_NAME: str = Field(default="Amazing API", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    APP_DEBUG: bool = Field(default=False, description="Debug mode")
    APP_ENV: str = Field(default="dev", description="Environment: dev, staging, prod")
    
    # Server Settings
    APP_HOST: str = Field(default="0.0.0.0", description="Server host")
    APP_PORT: int = Field(default=8000, description="Server port")
    
    # Database Settings
    DATABASE_URL: str = Field(..., description="Database connection URL")
    
    # Redis Settings (for caching/sessions)
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    
    # Security Settings
    JWT_SECRET_KEY: str = Field(..., description="Secret key for JWT and encryption")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration")
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")
    PASSWORD_SPECIAL_CHARS: str = Field(default="!@#$%^&*()_+-=[]{}|;:,.<>?", description="Special characters for password validation")
    
    # CORS Settings
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:8081", "http://localhost:3000"],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials in CORS")
    CORS_ALLOW_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        description="Allowed CORS methods"
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        default=["*"],
        description="Allowed CORS headers"
    )
    CORS_EXPOSE_HEADERS: List[str] = Field(
        default=["X-Total-Count", "X-Page-Count"],
        description="Exposed CORS headers"
    )
    CORS_MAX_AGE: int = Field(default=86400, description="CORS max age in seconds")
    
    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @field_validator("CORS_ALLOW_METHODS", mode="before")
    def assemble_cors_methods(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @field_validator("CORS_ALLOW_HEADERS", mode="before")
    def assemble_cors_headers(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @field_validator("CORS_EXPOSE_HEADERS", mode="before")
    def assemble_cors_expose_headers(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Email Settings (for notifications)
    SMTP_TLS: bool = Field(default=True, description="SMTP TLS enabled")
    SMTP_PORT: Optional[int] = Field(default=587, description="SMTP port")
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP host")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")
    EMAILS_FROM_EMAIL: Optional[str] = Field(default=None, description="From email address")
    EMAILS_FROM_NAME: Optional[str] = Field(default=None, description="From name")
    
    # File Upload Settings
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, description="Max file size in bytes (10MB)")
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"],
        description="Allowed file extensions"
    )
    UPLOAD_DIR: str = Field(default="uploads", description="Upload directory")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60, description="Rate limit per minute")
    RATE_LIMIT_REQUESTS_PER_HOUR: int = Field(default=1000, description="Rate limit per hour")
    
    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: str = Field(default="app.log", description="Log file name")
    LOG_TO_FILE: bool = Field(default=True, description="Enable logging to file")
    LOG_MAX_SIZE: int = Field(default=10 * 1024 * 1024, description="Max log file size")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Number of log backup files")
    
    # API Documentation
    DOCS_URL: str = Field(default="/docs", description="Swagger UI URL")
    REDOC_URL: str = Field(default="/redoc", description="ReDoc URL")
    OPENAPI_URL: str = Field(default="/openapi.json", description="OpenAPI schema URL")
    
    # Monitoring & Health Checks
    HEALTH_CHECK_INTERVAL: int = Field(default=30, description="Health check interval in seconds")
    METRICS_ENABLED: bool = Field(default=True, description="Enable metrics collection")
    
    # Celery Settings (for background tasks)
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1", description="Celery result backend")
    
    # Testing Settings
    TESTING: bool = Field(default=False, description="Testing mode")
    TEST_DATABASE_URL: Optional[str] = Field(default=None, description="Test database URL")
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=15, description="Default pagination size")
    MAX_PAGE_SIZE: int = Field(default=100, description="Maximum pagination size")
    
    # Cache Settings
    CACHE_TTL: int = Field(default=300, description="Default cache TTL in seconds")
    CACHE_ENABLED: bool = Field(default=True, description="Enable caching")
    
    @field_validator("JWT_SECRET_KEY", mode="before")
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("APP_ENV", mode="before")
    def validate_environment(cls, v: str) -> str:
        allowed = ["dev", "staging", "prod"]
        if v not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}")
        return v
    
    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "dev"
    
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "prod"
    
    @property
    def is_testing(self) -> bool:
        return self.TESTING
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()