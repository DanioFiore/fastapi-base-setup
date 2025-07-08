"""
Database session management module.

This module sets up the SQLModel engine using the provided DATABASE_URL,
initializes the database schema, and provides a session generator for
database operations.

Functions:
    init_db(): Initializes the database by creating all tables defined in SQLModel metadata.
    get_session(): Yields a new SQLModel session for use in database operations.

Raises:
    NotImplementedError: If DATABASE_URL is not set in the environment variables.

"""
import sqlmodel
from sqlmodel import Session, SQLModel

from .config import DATABASE_URL

if DATABASE_URL == "":
    raise NotImplementedError(
        "DATABASE_URL is not set. Please set it in the environment variables."
    )

engine = sqlmodel.create_engine(str(DATABASE_URL))


def init_db():
    """
    Initializes the database by creating all tables defined in the SQLModel metadata.
    This function prints a message indicating the initialization process and then
    creates all tables in the database using the provided engine and SQLModel metadata.
    """
    print("Initializing database...")
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Yields a new SQLModel session for use in database operations.
    This function creates a new session using the SQLModel engine and yields it.
    After the session is used, it is automatically closed."""
    with Session(engine) as session:
        yield session
        print("Session created.")
