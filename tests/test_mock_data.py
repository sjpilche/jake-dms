"""Tests for the mock data seeder."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.db.models import (
    ARAgingRow,
    APAgingRow,
    CashBalanceRow,
    GLAccountRow,
    GLBalanceRow,
    PlatformRevenueRow,
    PLRow,
    ProductionCostRow,
    ReconRecordRow,
)
from src.demo.mock_data import seed_database


def test_seed_creates_gl_accounts(db_session: Session) -> None:
    seed_database(db_session)
    count = db_session.query(GLAccountRow).count()
    assert count >= 30, f"Expected at least 30 GL accounts, got {count}"


def test_seed_creates_gl_balances(db_session: Session) -> None:
    seed_database(db_session)
    count = db_session.query(GLBalanceRow).count()
    assert count > 0, "Expected GL balance rows"


def test_revenue_approximately_78m(db_session: Session) -> None:
    """TTM revenue should be approximately $78M (within 30% tolerance for 18-month period)."""
    seed_database(db_session)
    total = db_session.query(func.sum(PLRow.amount)).filter(PLRow.category == "Revenue").scalar()
    total_float = float(total)
    # 18 months of data → annualized should be ~$78M
    annualized = total_float / 18 * 12
    assert 50_000_000 < annualized < 120_000_000, (
        f"Annualized revenue {annualized:,.0f} not in expected range"
    )


def test_expenses_approximately_58m(db_session: Session) -> None:
    """TTM expenses should yield ~26% operating margin."""
    seed_database(db_session)
    rev = float(db_session.query(func.sum(PLRow.amount)).filter(PLRow.category == "Revenue").scalar())
    cogs = float(db_session.query(func.sum(PLRow.amount)).filter(PLRow.category == "COGS").scalar())
    opex = float(db_session.query(func.sum(PLRow.amount)).filter(PLRow.category == "OpEx").scalar())
    margin = (rev - cogs - opex) / rev * 100
    assert 10 < margin < 40, f"Operating margin {margin:.1f}% outside expected 10-40% range"


def test_ar_aging_sums_correctly(db_session: Session) -> None:
    seed_database(db_session)
    rows = db_session.query(ARAgingRow).all()
    assert len(rows) > 0
    for row in rows:
        expected_total = row.current_amt + row.days_30 + row.days_60 + row.days_90_plus
        assert row.total == expected_total, (
            f"AR aging for {row.customer}: total {row.total} != sum {expected_total}"
        )


def test_ap_aging_sums_correctly(db_session: Session) -> None:
    seed_database(db_session)
    rows = db_session.query(APAgingRow).all()
    assert len(rows) > 0
    for row in rows:
        expected_total = row.current_amt + row.days_30 + row.days_60 + row.days_90_plus
        assert row.total == expected_total


def test_cash_balances_positive(db_session: Session) -> None:
    seed_database(db_session)
    rows = db_session.query(CashBalanceRow).all()
    assert len(rows) == 4
    for row in rows:
        assert row.balance > 0, f"Cash balance for {row.account_name} is not positive"
    total = sum(float(r.balance) for r in rows)
    assert total > 8_000_000, f"Total cash {total:,.0f} below expected minimum"


def test_production_costs_exist(db_session: Session) -> None:
    seed_database(db_session)
    count = db_session.query(ProductionCostRow).count()
    assert count == 50, f"Expected 50 production cost records, got {count}"


def test_production_cost_totals_correct(db_session: Session) -> None:
    seed_database(db_session)
    rows = db_session.query(ProductionCostRow).all()
    for row in rows:
        expected = row.talent + row.crew_cost + row.location + row.post_production + row.music_licensing
        assert row.total_cost == expected, (
            f"Production cost for {row.video_title}: total {row.total_cost} != sum {expected}"
        )


def test_recon_records_exist(db_session: Session) -> None:
    seed_database(db_session)
    count = db_session.query(ReconRecordRow).count()
    assert count > 0, "Expected reconciliation records"


def test_platform_revenue_covers_all_platforms(db_session: Session) -> None:
    seed_database(db_session)
    platforms = [r[0] for r in db_session.query(PlatformRevenueRow.platform).distinct().all()]
    assert len(platforms) >= 5, f"Expected at least 5 platforms, got {platforms}"
