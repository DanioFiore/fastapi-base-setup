"""
Database configuration module.

This module sets up the SQLAlchemy Base class for declarative models and retrieves
the database connection URL from the application settings.

Attributes:
    DATABASE_URL (str): The database connection string, loaded from application settings.
    Base (DeclarativeMeta): The base class for all SQLAlchemy ORM models.
"""
from sqlalchemy.ext.declarative import declarative_base

from core.config import settings

DATABASE_URL = settings.DATABASE_URL
Base = declarative_base()
