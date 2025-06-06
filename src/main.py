from fastapi import FastAPI
from api.users import router as users_router
from api.auth.routing import router as auth_router
from db.session import init_db
from contextlib import asynccontextmanager
from core.config import settings
from middleware.setup import setup_middleware, setup_development_middleware, setup_production_middleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database connection
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="A magical API for managing your finances",
    version=settings.APP_VERSION,
    docs_url=settings.APP_ENV != "prod" and settings.DOCS_URL or None,
    lifespan=lifespan
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
    return {"status": "ok"}
