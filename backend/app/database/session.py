"""SQLAlchemy engine, session factory and table initialisation.

The prototype uses a single SQLite database file under ``data/processed/``
(see backend/app/config.py). There is exactly one engine and one
``SessionLocal`` factory used across the app.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import DATABASE_URL

# check_same_thread=False: SQLite may be used from multiple threads (FastAPI).
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def init_db() -> None:
    """Create all tables (idempotent). Imports models so metadata is populated."""
    from backend.app.database import models  # noqa: F401

    models.Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a database session.

    Declared here so Day 3 routes can reuse it. Not wired to FastAPI yet.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()