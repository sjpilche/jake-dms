"""Tests for the Intacct XML API client."""

from __future__ import annotations

import pytest

from src.core.intacct_client import IntacctClient, IntacctError


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> IntacctClient:
    monkeypatch.setenv("INTACCT_MOCK_MODE", "true")
    monkeypatch.setenv("DEMO_MODE", "true")
    from src.core.config import get_settings
    get_settings.cache_clear()
    return IntacctClient()


@pytest.mark.asyncio
async def test_mock_cash_balances(client: IntacctClient) -> None:
    balances = await client.get_cash_balances()
    assert len(balances) == 4
    assert balances[0]["BANKNAME"] == "JPMorgan Chase"
    total = sum(float(b["CURRENTBALANCE"]) for b in balances)
    assert total > 8_000_000


@pytest.mark.asyncio
async def test_mock_ar_aging(client: IntacctClient) -> None:
    ar = await client.get_ar_aging()
    assert len(ar) == 2
    assert ar[0]["CUSTOMERNAME"] == "Google/YouTube"


@pytest.mark.asyncio
async def test_mock_create(client: IntacctClient) -> None:
    result = await client.create("TESTOBJ", {"field1": "value1"})
    assert result["RECORDNO"] == "MOCK-001"
    assert result["field1"] == "value1"


@pytest.mark.asyncio
async def test_mock_stat_journal(client: IntacctClient) -> None:
    result = await client.create_statistical_journal(
        journal_id="TEST",
        entries=[{"account_no": "STAT-001", "amount": "100", "memo": "test"}],
        description="Test journal",
    )
    assert result["RECORDNO"] == "MOCK-STAT-001"


def test_build_envelope(client: IntacctClient) -> None:
    envelope = client._build_envelope("<readByQuery><object>TEST</object></readByQuery>")
    assert "<senderid>" in envelope
    assert "<readByQuery>" in envelope
    assert "TEST" in envelope


def test_check_errors_success() -> None:
    parsed = {"response": {"operation": {"result": {"status": "success"}}}}
    IntacctClient._check_errors(parsed)  # Should not raise


def test_check_errors_failure() -> None:
    parsed = {
        "response": {"operation": {"result": {
            "status": "failure",
            "errormessage": {"error": {
                "errorno": "BL123",
                "description2": "Test error",
            }},
        }}},
    }
    with pytest.raises(IntacctError) as exc_info:
        IntacctClient._check_errors(parsed)
    assert "BL123" in str(exc_info.value)
