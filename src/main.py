"""Main application entry point for the FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.auth.routing import router as auth_router
from api.users import router as users_router
from core.config import settings
from db.session import init_db
from middleware.setup import (
    setup_development_middleware,
    setup_middleware,
    setup_production_middleware,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Application lifespan event handler to initialize the database.
    This function is called when the application starts up and ensures
    that the database is initialized before handling any requests."""
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Fast API base setup with user authentication and management.",
    version=settings.APP_VERSION,
    docs_url=settings.APP_ENV != "prod" and settings.DOCS_URL or None,
    lifespan=lifespan,
)

# Setup middleware based on environment
if settings.is_development:
    setup_development_middleware(app)
elif settings.is_production:
    setup_production_middleware(app)
else:
    # Default middleware setup for staging
    setup_middleware(app)

app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])

@app.get("/healthz")
def read_api_health():
    """Health check endpoint to verify the API is running."""
    return {"status": "ok"}
