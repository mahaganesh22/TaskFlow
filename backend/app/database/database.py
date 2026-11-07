
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


# 1. Create the database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)


# 2. Create the session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


# 3. Create the base class for database models
class Base(DeclarativeBase):
    pass


# 4. Database dependency for FastAPI
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
