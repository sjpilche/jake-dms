"""Tests for the FastAPI endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _demo_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("INTACCT_MOCK_MODE", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "")
    from src.core.config import get_settings
    get_settings.cache_clear()


@pytest.fixture
def api_client() -> TestClient:
    from src.api.main import app
    return TestClient(app)


def test_health(api_client: TestClient) -> None:
    resp = api_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "jake-dms"


def test_status(api_client: TestClient) -> None:
    resp = api_client.get("/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "scheduler_jobs" in data


def test_trigger_recon(api_client: TestClient) -> None:
    resp = api_client.post("/agents/recon/run")
    assert resp.status_code == 200
    assert resp.json()["status"] == "started"


def test_trigger_cash(api_client: TestClient) -> None:
    resp = api_client.post("/agents/cash/run")
    assert resp.status_code == 200
    assert resp.json()["status"] == "started"


def test_trigger_roi(api_client: TestClient) -> None:
    resp = api_client.post("/agents/roi/run")
    assert resp.status_code == 200
    assert resp.json()["status"] == "started"


def test_trigger_concentration(api_client: TestClient) -> None:
    resp = api_client.post("/agents/concentration/run")
    assert resp.status_code == 200
    assert resp.json()["status"] == "started"


def test_trigger_report(api_client: TestClient) -> None:
    resp = api_client.post("/agents/report/generate")
    assert resp.status_code == 200
    assert resp.json()["status"] == "started"
