"""Pytest fixtures for Jake-DMS tests."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import Base


@pytest.fixture(autouse=True)
def _set_demo_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests always run in demo mode with in-memory DB."""
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test_jake_dms.db")
    monkeypatch.setenv("YOUTUBE_API_KEY", "")


@pytest.fixture
def db_session() -> Session:
    """Create an in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    yield session
    session.close()
