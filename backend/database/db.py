"""
Database connection, session management, and engine configuration.
Supports SQLite (development/testing) and PostgreSQL (production).
"""
import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from config.settings import settings

Base = declarative_base()


def create_db_engine(db_url: str = settings.DATABASE_URL) -> Engine:
    """
    Creates and configures a SQLAlchemy engine with safe dialect-specific defaults.
    Ensures directories for SQLite database files exist prior to connection.
    """
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

        # Extract file path from sqlite url (e.g. sqlite:///./opthire.db or sqlite:///C:/path/file.db)
        clean_path = db_url.replace("sqlite:///", "")
        if clean_path and clean_path != ":memory:" and not clean_path.startswith("?"):
            db_file_path = Path(clean_path).resolve()
            db_file_path.parent.mkdir(parents=True, exist_ok=True)

        return create_engine(
            db_url,
            connect_args=connect_args,
            echo=settings.DEBUG,
        )

    # Production database (PostgreSQL / MySQL) connection pool configuration
    return create_engine(
        db_url,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a request-scoped database session.
    Guarantees session cleanup upon request termination.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(engine_instance: Engine = engine) -> None:
    """
    Initializes database tables defined on Base metadata.
    """
    import database.models  # Ensure all model definitions are registered
    Base.metadata.create_all(bind=engine_instance)

