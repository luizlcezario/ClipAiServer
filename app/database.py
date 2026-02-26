"""
Database configuration and session management.

This module sets up SQLAlchemy ORM configuration, database engine,
and session factory for the application.
"""

from typing import Generator
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings


# Create database engine
engine: Engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.

    Yields:
        Session: SQLAlchemy database session

    Example:
        @app.get("/clips")
        def get_clips(db: Session = Depends(get_db)):
            return db.query(ClipJob).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.

    This function should be called at application startup.
    """
    from app.models.clip_job import Base
    Base.metadata.create_all(bind=engine)
