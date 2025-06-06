from core.config import settings
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = settings.DATABASE_URL
Base = declarative_base()