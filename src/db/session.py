import sqlmodel
from .config import DATABASE_URL
from sqlmodel import SQLModel, Session

if DATABASE_URL == "":
    raise NotImplementedError(
        "DATABASE_URL is not set. Please set it in the environment variables."
    )

engine = sqlmodel.create_engine(str(DATABASE_URL))

def init_db():
    print("Initializing database...")
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
        print("Session created.")
