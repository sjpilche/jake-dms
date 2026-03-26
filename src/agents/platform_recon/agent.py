"""Agent 3: Platform Revenue Reconciliation.

Orchestrates daily reconciliation of YouTube/Meta estimated revenue
against Intacct GL entries. Flags variances > 5%, writes statistical
journals, sends Telegram summaries.

Schedule: daily at 7:00 AM PT.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from loguru import logger

from src.agents.platform_recon.models import PlatformEstimate, ReconResult
from src.core.config import get_settings
from src.core.intacct_client import IntacctClient
from src.core.meta_client import MetaClient
from src.core.telegram_bot import TelegramNotifier
from src.core.youtube_analytics import YouTubeAnalyticsClient

VARIANCE_THRESHOLD = Decimal("5.0")


class PlatformReconAgent:
    """Reconcile platform revenue estimates against Intacct GL deposits."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.intacct = IntacctClient()
        self.youtube = YouTubeAnalyticsClient()
        self.meta = MetaClient()
        self.telegram = TelegramNotifier()

    async def run_daily(self, target_date: date | None = None) -> list[ReconResult]:
        """Execute daily reconciliation cycle."""
        target = target_date or date.today()
        period = target.strftime("%Y-%m")
        logger.info(f"Running platform reconciliation for {period}")

        # Step 1: Get estimated revenue from platforms
        estimates = await self._collect_estimates(target)

        # Step 2: Get actual GL deposits from Intacct
        actuals = await self._collect_actuals(period)

        # Step 3: Match and reconcile
        results = self._reconcile(estimates, actuals)

        # Step 4: Write stat journal for flagged items
        flagged = [r for r in results if r.status == "Flagged"]
        if flagged:
            await self._write_stat_journal(flagged, period)

        # Step 5: Send Telegram summary
        await self._send_summary(results)

        logger.info(
            f"Reconciliation complete: {len(results)} records, "
            f"{len(flagged)} flagged"
        )
        return results

    async def _collect_estimates(self, target: date) -> list[PlatformEstimate]:
        """Pull estimated revenue from YouTube and Meta APIs."""
        estimates: list[PlatformEstimate] = []
        month_start = target.replace(day=1)
        period = target.strftime("%Y-%m")

        # YouTube
        yt_metrics = await self.youtube.get_daily_metrics(month_start, target)
        yt_total = sum((m.estimated_revenue for m in yt_metrics), Decimal("0"))
        estimates.append(PlatformEstimate(
            platform="YouTube", period=period,
            estimated_revenue=yt_total, source="youtube_analytics",
        ))

        # Meta
        meta_metrics = await self.meta.get_daily_metrics(month_start, target)
        meta_total = sum((m.estimated_revenue for m in meta_metrics), Decimal("0"))
        estimates.append(PlatformEstimate(
            platform="Facebook", period=period,
            estimated_revenue=meta_total, source="meta_api",
        ))

        return estimates

    async def _collect_actuals(self, period: str) -> dict[str, Decimal]:
        """Pull actual deposits from Intacct GL."""
        # In production: query Intacct for deposits from Google/Meta vendors
        # In mock mode: generate realistic actuals
        gl_entries = await self.intacct.get_gl_balances(period)

        # Map vendor deposits to platforms
        actuals: dict[str, Decimal] = {"YouTube": Decimal("0"), "Facebook": Decimal("0")}

        for entry in gl_entries:
            amount = Decimal(str(entry.get("AMOUNT", "0")))
            desc = str(entry.get("ACCOUNTTITLE", "")).lower()
            if "google" in desc or "youtube" in desc:
                actuals["YouTube"] += amount
            elif "meta" in desc or "facebook" in desc:
                actuals["Facebook"] += amount

        # If mock mode and no GL data, generate mock actuals
        if self.settings.INTACCT_MOCK_MODE and all(v == 0 for v in actuals.values()):
            import random
            rng = random.Random(hash(period))
            actuals["YouTube"] = Decimal(str(round(rng.uniform(2_200_000, 3_200_000), 2)))
            actuals["Facebook"] = Decimal(str(round(rng.uniform(500_000, 900_000), 2)))

        return actuals

    def _reconcile(
        self,
        estimates: list[PlatformEstimate],
        actuals: dict[str, Decimal],
    ) -> list[ReconResult]:
        """Compare estimates to actuals, flag variances > threshold."""
        results: list[ReconResult] = []

        for est in estimates:
            actual = actuals.get(est.platform, Decimal("0"))
            variance = actual - est.estimated_revenue
            variance_pct = (
                (variance / est.estimated_revenue * 100)
                if est.estimated_revenue != 0
                else Decimal("0")
            )
            status = "Flagged" if abs(variance_pct) > VARIANCE_THRESHOLD else "Matched"

            results.append(ReconResult(
                platform=est.platform,
                period=est.period,
                estimated_revenue=est.estimated_revenue,
                actual_received=actual,
                variance=variance,
                variance_pct=variance_pct,
                status=status,
            ))

        return results

    async def _write_stat_journal(
        self, flagged: list[ReconResult], period: str
    ) -> None:
        """Write flagged reconciliation items to Intacct as statistical journal."""
        entries = []
        for r in flagged:
            entries.append({
                "account_no": "STAT-RECON",
                "amount": str(r.variance),
                "memo": f"Recon variance: {r.platform} {r.period} ({r.variance_pct:+.1f}%)",
            })
        await self.intacct.create_statistical_journal(
            journal_id="RECON",
            entries=entries,
            description=f"Platform reconciliation flags for {period}",
        )

    async def _send_summary(self, results: list[ReconResult]) -> None:
        """Send Telegram reconciliation summary."""
        matched = sum(1 for r in results if r.status == "Matched")
        flagged_items = [r for r in results if r.status == "Flagged"]
        total_variance = sum(float(r.variance) for r in results)

        details = [
            {
                "platform": r.platform,
                "period": r.period,
                "variance": float(r.variance),
                "variance_pct": float(r.variance_pct),
            }
            for r in flagged_items
        ]
        await self.telegram.send_recon_summary(matched, len(flagged_items), total_variance, details)
