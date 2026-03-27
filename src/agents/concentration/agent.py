"""Agent 6: Revenue Concentration Monitor.

Tracks platform vs non-platform revenue mix against the 40% target.
Calculates Herfindahl index. Alerts on concentration thresholds.

Schedule: monthly on 5th at 9:00 AM PT (after close).
"""

from __future__ import annotations

from decimal import Decimal

from loguru import logger

from src.agents.concentration.models import ConcentrationAlert, ConcentrationMetrics
from src.core.config import get_settings
from src.core.intacct_client import IntacctClient
from src.core.telegram_bot import TelegramNotifier

# Platform revenue sources (ad revenue from these = "platform dependent")
PLATFORM_SOURCES = {"YouTube", "Facebook", "TikTok", "Snap"}


class ConcentrationMonitorAgent:
    """Monitor revenue concentration and diversification metrics."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.intacct = IntacctClient()
        self.telegram = TelegramNotifier()

    async def run_monthly(self, period: str = "YTD") -> ConcentrationMetrics | None:
        """Calculate concentration metrics and send alerts."""
        try:
            logger.info(f"Running concentration analysis for {period}")

            revenue_by_source = await self._get_revenue_by_source()
            metrics = self._calculate_metrics(revenue_by_source, period)
            alerts = self._evaluate_alerts(metrics)

            # Send Telegram alerts
            for alert in alerts:
                if alert.level in ("RED", "YELLOW"):
                    await self.telegram.send_concentration_alert(
                        platform_pct=float(metrics.platform_revenue_pct),
                        largest_source=metrics.largest_source,
                        largest_pct=float(metrics.largest_source_pct),
                    )
                    break  # One summary alert is enough

            logger.info(
                f"Concentration: platform={metrics.platform_revenue_pct:.1f}%, "
                f"HHI={metrics.herfindahl_index:.0f}, alert={metrics.alert_level}"
            )
            return metrics
        except Exception as exc:
            logger.exception(f"ConcentrationMonitorAgent.run_monthly failed: {exc}")
            return None

    async def _get_revenue_by_source(self) -> dict[str, Decimal]:
        """Get revenue breakdown by source from Intacct."""
        if self.settings.DEMO_MODE:
            return self._mock_revenue()

        # In production: read dimension-tagged revenue from Intacct
        gl_data = await self.intacct.read_by_query(
            "GLENTRY",
            query="ACCOUNTNO LIKE '4%'",  # Revenue accounts
            fields=["ACCOUNTNO", "ACCOUNTTITLE", "AMOUNT", "DEPARTMENT"],
        )

        by_source: dict[str, Decimal] = {}
        for entry in gl_data:
            source = entry.get("DEPARTMENT", "Other")
            amount = Decimal(str(entry.get("AMOUNT", "0")))
            by_source[source] = by_source.get(source, Decimal("0")) + abs(amount)

        return by_source

    def _calculate_metrics(
        self,
        revenue_by_source: dict[str, Decimal],
        period: str,
    ) -> ConcentrationMetrics:
        """Calculate all concentration metrics deterministically."""
        total = sum(revenue_by_source.values())
        if total == 0:
            total = Decimal("1")  # Avoid division by zero

        # Platform vs non-platform
        platform_rev = sum(
            v for k, v in revenue_by_source.items() if k in PLATFORM_SOURCES
        )
        platform_pct = platform_rev / total * 100
        non_platform_pct = Decimal("100") - platform_pct

        # Herfindahl index (sum of squared market shares)
        hhi = Decimal("0")
        for v in revenue_by_source.values():
            share = v / total * 100
            hhi += share * share

        # Largest single source
        largest_source = max(revenue_by_source, key=revenue_by_source.get)  # type: ignore[arg-type]
        largest_pct = revenue_by_source[largest_source] / total * 100

        # Alert level
        if platform_pct > 50:
            alert = "RED"
        elif largest_pct > 30 or platform_pct > 40:
            alert = "YELLOW"
        else:
            alert = "GREEN"

        return ConcentrationMetrics(
            period=period,
            platform_revenue_pct=Decimal(str(round(float(platform_pct), 2))),
            non_platform_revenue_pct=Decimal(str(round(float(non_platform_pct), 2))),
            herfindahl_index=Decimal(str(round(float(hhi), 0))),
            largest_source=largest_source,
            largest_source_pct=Decimal(str(round(float(largest_pct), 2))),
            revenue_by_source=revenue_by_source,
            alert_level=alert,
        )

    @staticmethod
    def _evaluate_alerts(metrics: ConcentrationMetrics) -> list[ConcentrationAlert]:
        """Evaluate alert thresholds."""
        alerts: list[ConcentrationAlert] = []

        if metrics.platform_revenue_pct > 50:
            alerts.append(ConcentrationAlert(
                level="RED",
                metric="platform_concentration",
                value=metrics.platform_revenue_pct,
                threshold=Decimal("50"),
                message=f"Platform revenue at {metrics.platform_revenue_pct:.0f}% — above 50% RED threshold",
            ))
        elif metrics.platform_revenue_pct > 40:
            alerts.append(ConcentrationAlert(
                level="YELLOW",
                metric="platform_concentration",
                value=metrics.platform_revenue_pct,
                threshold=Decimal("40"),
                message=f"Platform revenue at {metrics.platform_revenue_pct:.0f}% — above 40% target",
            ))

        if metrics.largest_source_pct > 30:
            alerts.append(ConcentrationAlert(
                level="YELLOW",
                metric="single_source_concentration",
                value=metrics.largest_source_pct,
                threshold=Decimal("30"),
                message=f"{metrics.largest_source} at {metrics.largest_source_pct:.0f}% — above 30% threshold",
            ))

        return alerts

    @staticmethod
    def _mock_revenue() -> dict[str, Decimal]:
        """Mock revenue by source for demo mode."""
        return {
            "YouTube": Decimal("32000000"),
            "Facebook": Decimal("8000000"),
            "TikTok": Decimal("1500000"),
            "Brand Deals": Decimal("18000000"),
            "Licensing": Decimal("12000000"),
            "Merchandise": Decimal("5000000"),
            "Other": Decimal("1500000"),
        }
