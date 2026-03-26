"""Tests for all 5 production agents (mock/demo mode)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from src.agents.cash_forecast.agent import CashForecastAgent
from src.agents.concentration.agent import ConcentrationMonitorAgent
from src.agents.content_roi.agent import ContentROIAgent
from src.agents.investor_report.agent import InvestorReportAgent
from src.agents.platform_recon.agent import PlatformReconAgent


@pytest.fixture(autouse=True)
def _demo_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("INTACCT_MOCK_MODE", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "")
    from src.core.config import get_settings
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Platform Reconciliation Agent
# ---------------------------------------------------------------------------

class TestPlatformReconAgent:
    @pytest.mark.asyncio
    async def test_run_daily_returns_results(self) -> None:
        agent = PlatformReconAgent()
        results = await agent.run_daily(target_date=date(2026, 3, 15))
        assert len(results) == 2  # YouTube + Facebook
        for r in results:
            assert r.platform in ("YouTube", "Facebook")
            assert r.status in ("Matched", "Flagged")

    @pytest.mark.asyncio
    async def test_reconcile_flags_large_variance(self) -> None:
        agent = PlatformReconAgent()
        from src.agents.platform_recon.models import PlatformEstimate
        estimates = [
            PlatformEstimate(
                platform="YouTube", period="2026-03",
                estimated_revenue=Decimal("100000"), source="test",
            ),
        ]
        actuals = {"YouTube": Decimal("120000")}  # 20% variance
        results = agent._reconcile(estimates, actuals)
        assert results[0].status == "Flagged"
        assert results[0].variance_pct == Decimal("20.00")

    @pytest.mark.asyncio
    async def test_reconcile_matches_small_variance(self) -> None:
        agent = PlatformReconAgent()
        from src.agents.platform_recon.models import PlatformEstimate
        estimates = [
            PlatformEstimate(
                platform="YouTube", period="2026-03",
                estimated_revenue=Decimal("100000"), source="test",
            ),
        ]
        actuals = {"YouTube": Decimal("102000")}  # 2% variance
        results = agent._reconcile(estimates, actuals)
        assert results[0].status == "Matched"


# ---------------------------------------------------------------------------
# Content ROI Agent
# ---------------------------------------------------------------------------

class TestContentROIAgent:
    def test_mock_production_costs(self) -> None:
        costs = ContentROIAgent._mock_production_costs()
        assert len(costs) == 50
        for vid, data in costs.items():
            assert data["total_cost"] > 0

    def test_mock_video_metrics(self) -> None:
        metrics = ContentROIAgent._mock_video_metrics()
        assert len(metrics) == 50
        for vid, data in metrics.items():
            assert data["views"] > 0

    def test_aggregate_by_format(self) -> None:
        agent = ContentROIAgent()
        from src.agents.content_roi.models import EpisodeROI
        episodes = [
            EpisodeROI(
                episode_id="E1", youtube_video_id="V1", title="Test",
                content_format="Long-Form", crew_id="A", publish_date=date(2026, 1, 1),
                production_cost=Decimal("20000"), lifetime_views=5_000_000,
                lifetime_revenue=Decimal("22500"), cost_per_view=Decimal("0.004"),
                cost_per_1k_views=Decimal("4.00"), revenue_per_episode=Decimal("22500"),
                margin=Decimal("11.11"), roi=Decimal("12.50"),
            ),
            EpisodeROI(
                episode_id="E2", youtube_video_id="V2", title="Test 2",
                content_format="Long-Form", crew_id="B", publish_date=date(2026, 1, 2),
                production_cost=Decimal("15000"), lifetime_views=8_000_000,
                lifetime_revenue=Decimal("36000"), cost_per_view=Decimal("0.001875"),
                cost_per_1k_views=Decimal("1.88"), revenue_per_episode=Decimal("36000"),
                margin=Decimal("58.33"), roi=Decimal("140.00"),
            ),
        ]
        reports = agent._aggregate_by_format(episodes)
        assert len(reports) == 1
        assert reports[0].content_format == "Long-Form"
        assert reports[0].episode_count == 2
        assert reports[0].total_production_cost == Decimal("35000")


# ---------------------------------------------------------------------------
# Cash Forecast Agent
# ---------------------------------------------------------------------------

class TestCashForecastAgent:
    @pytest.mark.asyncio
    async def test_run_daily_returns_13_weeks(self) -> None:
        agent = CashForecastAgent()
        forecast = await agent.run_daily()
        assert len(forecast) == 13
        assert forecast[0].week_number == 1
        assert forecast[-1].week_number == 13

    def test_check_alerts(self) -> None:
        from src.agents.cash_forecast.models import WeeklyForecast
        from datetime import date
        # Create a forecast with one week below minimum
        forecast = [
            WeeklyForecast(
                week_number=1, week_start=date(2026, 3, 26),
                opening_cash=Decimal("500000"), platform_inflows=Decimal("100000"),
                brand_deal_inflows=Decimal("50000"), licensing_inflows=Decimal("20000"),
                other_inflows=Decimal("10000"), total_inflows=Decimal("180000"),
                payroll=Decimal("500000"), production=Decimal("100000"),
                talent=Decimal("50000"), facilities=Decimal("30000"),
                technology=Decimal("20000"), marketing=Decimal("40000"),
                ga=Decimal("30000"), total_outflows=Decimal("770000"),
                net_change=Decimal("-590000"), closing_cash=Decimal("-90000"),
                below_minimum=True,
            ),
        ]
        alerts = CashForecastAgent._check_alerts(forecast)
        assert len(alerts) == 1
        assert alerts[0].alert_type == "below_minimum"


# ---------------------------------------------------------------------------
# Concentration Monitor Agent
# ---------------------------------------------------------------------------

class TestConcentrationAgent:
    @pytest.mark.asyncio
    async def test_run_monthly_returns_metrics(self) -> None:
        agent = ConcentrationMonitorAgent()
        metrics = await agent.run_monthly()
        assert metrics.platform_revenue_pct > 0
        assert metrics.herfindahl_index > 0
        assert metrics.alert_level in ("GREEN", "YELLOW", "RED")

    def test_calculate_metrics_red_alert(self) -> None:
        agent = ConcentrationMonitorAgent()
        revenue = {
            "YouTube": Decimal("60000000"),
            "Facebook": Decimal("10000000"),
            "Brand Deals": Decimal("10000000"),
            "Other": Decimal("20000000"),
        }
        metrics = agent._calculate_metrics(revenue, "2026-YTD")
        assert metrics.alert_level == "RED"
        assert metrics.platform_revenue_pct == Decimal("70.00")

    def test_calculate_metrics_green(self) -> None:
        agent = ConcentrationMonitorAgent()
        revenue = {
            "YouTube": Decimal("15000000"),
            "Facebook": Decimal("5000000"),
            "Brand Deals": Decimal("25000000"),
            "Licensing": Decimal("25000000"),
            "Other": Decimal("30000000"),
        }
        metrics = agent._calculate_metrics(revenue, "2026-YTD")
        assert metrics.alert_level == "GREEN"

    def test_herfindahl_index(self) -> None:
        agent = ConcentrationMonitorAgent()
        # Single source → HHI should be 10000
        metrics = agent._calculate_metrics(
            {"YouTube": Decimal("100")}, "test"
        )
        assert metrics.herfindahl_index == Decimal("10000")


# ---------------------------------------------------------------------------
# Investor Report Agent
# ---------------------------------------------------------------------------

class TestInvestorReportAgent:
    @pytest.mark.asyncio
    async def test_generate_returns_package(self) -> None:
        agent = InvestorReportAgent()
        package = await agent.generate(period="2026-02")
        assert package.period == "2026-02"
        assert package.total_revenue > 0
        assert package.gross_margin_pct > 0
        assert package.operating_margin_pct > 0

    @pytest.mark.asyncio
    async def test_excel_generation(self) -> None:
        agent = InvestorReportAgent()
        package = await agent._build_package("2026-02")
        output = agent._generate_excel(package)
        assert output.format == "excel"
        assert output.size_bytes > 0

    @pytest.mark.asyncio
    async def test_pdf_generation(self) -> None:
        agent = InvestorReportAgent()
        package = await agent._build_package("2026-02")
        output = agent._generate_pdf(package)
        assert output.format == "pdf"
        assert output.size_bytes > 0
