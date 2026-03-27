"""Database engine setup — sync for Streamlit, async for future agents."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from loguru import logger
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import get_settings
from src.db.models import Base


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


def get_session() -> Session:
    """Get a raw session. Prefer get_db() context manager for auto-cleanup."""
    return get_session_factory()()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context-managed session with automatic commit/rollback and close."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all tables if they don't exist."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("Database initialized")


def db_exists() -> bool:
    """Check if the SQLite database file exists and has tables."""
    settings = get_settings()
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        db_path = url.replace("sqlite:///", "").replace("./", "")
        return Path(db_path).exists()
    return True
