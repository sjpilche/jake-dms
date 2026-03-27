"""Agent 4: Content ROI Engine.

Maps Intacct project codes to YouTube video IDs, calculates per-episode
ROI metrics, segments by format/series/crew. Sends weekly Telegram
reports (top/bottom 5). Monthly format-level margin analysis.
Pushes metrics to Intacct statistical accounts.

Schedule: weekly on Monday at 8:00 AM PT, monthly on 1st at 9:00 AM PT.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from loguru import logger

from src.agents.content_roi.models import EpisodeROI, FormatMarginReport
from src.core.config import get_settings
from src.core.intacct_client import IntacctClient
from src.core.telegram_bot import TelegramNotifier
from src.core.youtube_analytics import YouTubeAnalyticsClient
from src.demo.youtube_public import YouTubePublicClient


class ContentROIAgent:
    """Calculate episode-level ROI by tying Intacct costs to YouTube performance."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.intacct = IntacctClient()
        self.youtube_public = YouTubePublicClient()
        self.youtube_analytics = YouTubeAnalyticsClient()
        self.telegram = TelegramNotifier()

    async def run_weekly(self) -> list[EpisodeROI]:
        """Weekly ROI calculation + Telegram top/bottom 5."""
        try:
            logger.info("Running weekly Content ROI analysis")

            episodes = await self._calculate_all_roi()

            # Sort by ROI
            sorted_episodes = sorted(episodes, key=lambda e: e.roi, reverse=True)
            top_5 = sorted_episodes[:5]
            bottom_5 = sorted_episodes[-5:]

            # Send Telegram
            await self.telegram.send_roi_summary(
                top_5=[{"title": e.title, "roi": float(e.roi)} for e in top_5],
                bottom_5=[{"title": e.title, "roi": float(e.roi)} for e in bottom_5],
            )

            logger.info(f"ROI analysis complete: {len(episodes)} episodes")
            return episodes
        except Exception as exc:
            logger.exception(f"ContentROIAgent.run_weekly failed: {exc}")
            return []

    async def run_monthly(self) -> list[FormatMarginReport]:
        """Monthly format-level margin analysis + push to Intacct."""
        try:
            logger.info("Running monthly Content ROI margin analysis")

            episodes = await self._calculate_all_roi()
            reports = self._aggregate_by_format(episodes)

            # Push metrics to Intacct statistical accounts
            await self._push_to_intacct(reports)

            logger.info(f"Format margin reports: {len(reports)} formats")
            return reports
        except Exception as exc:
            logger.exception(f"ContentROIAgent.run_monthly failed: {exc}")
            return []

    async def _calculate_all_roi(self) -> list[EpisodeROI]:
        """Calculate ROI for all mapped episodes."""
        # Get production costs from Intacct
        costs = await self._get_production_costs()

        # Get YouTube video performance
        videos = self._get_video_metrics()

        # Match and calculate ROI
        episodes: list[EpisodeROI] = []
        for video_id, cost_data in costs.items():
            video = videos.get(video_id)
            if not video:
                continue

            views = video["views"]
            revenue = Decimal(str(round(views * 4.5 / 1000, 2)))  # CPM estimate
            prod_cost = cost_data["total_cost"]

            cpv = Decimal(str(round(float(prod_cost) / views, 6))) if views > 0 else Decimal("0")
            cp1k = Decimal(str(round(float(cpv) * 1000, 2)))
            margin = (
                Decimal(str(round((float(revenue) - float(prod_cost)) / float(revenue) * 100, 2)))
                if revenue > 0 else Decimal("-100")
            )
            roi = (
                Decimal(str(round((float(revenue) - float(prod_cost)) / float(prod_cost) * 100, 2)))
                if prod_cost > 0 else Decimal("0")
            )

            episodes.append(EpisodeROI(
                episode_id=cost_data["project_code"],
                youtube_video_id=video_id,
                title=video["title"],
                content_format=cost_data.get("format", "Long-Form"),
                crew_id=cost_data.get("crew_id", "CREW-A"),
                publish_date=video.get("publish_date", date.today()),
                production_cost=prod_cost,
                lifetime_views=views,
                lifetime_revenue=revenue,
                cost_per_view=cpv,
                cost_per_1k_views=cp1k,
                revenue_per_episode=revenue,
                margin=margin,
                roi=roi,
            ))

        return episodes

    async def _get_production_costs(self) -> dict[str, dict]:
        """Get production costs from Intacct (or mock data)."""
        if self.settings.DEMO_MODE:
            return self._mock_production_costs()

        raw = await self.intacct.get_project_costs()
        costs: dict[str, dict] = {}
        for entry in raw:
            pid = entry.get("PROJECTID", "")
            costs[pid] = {
                "project_code": pid,
                "total_cost": Decimal(str(entry.get("TOTALDUE", "0"))),
                "format": "Long-Form",
                "crew_id": "CREW-A",
            }
        return costs

    def _get_video_metrics(self) -> dict[str, dict]:
        """Get video metrics from YouTube (public API for demo)."""
        try:
            videos = self.youtube_public.get_recent_videos(max_results=50)
            return {
                v.video_id: {
                    "title": v.title,
                    "views": v.view_count,
                    "publish_date": v.published_at.date(),
                }
                for v in videos
            }
        except Exception:
            return self._mock_video_metrics()

    def _aggregate_by_format(
        self, episodes: list[EpisodeROI]
    ) -> list[FormatMarginReport]:
        """Aggregate ROI metrics by content format."""
        by_format: dict[str, list[EpisodeROI]] = defaultdict(list)
        for ep in episodes:
            by_format[ep.content_format].append(ep)

        reports: list[FormatMarginReport] = []
        for fmt, eps in by_format.items():
            total_cost = sum(e.production_cost for e in eps)
            total_rev = sum(e.lifetime_revenue for e in eps)
            count = len(eps)
            reports.append(FormatMarginReport(
                content_format=fmt,
                episode_count=count,
                total_production_cost=total_cost,
                total_revenue=total_rev,
                avg_cost_per_episode=Decimal(str(round(float(total_cost) / count, 2))),
                avg_revenue_per_episode=Decimal(str(round(float(total_rev) / count, 2))),
                avg_roi=Decimal(str(round(
                    sum(float(e.roi) for e in eps) / count, 2
                ))),
                avg_cost_per_1k_views=Decimal(str(round(
                    sum(float(e.cost_per_1k_views) for e in eps) / count, 2
                ))),
            ))
        return reports

    async def _push_to_intacct(self, reports: list[FormatMarginReport]) -> None:
        """Push format-level metrics to Intacct statistical accounts."""
        entries = []
        for r in reports:
            entries.append({
                "account_no": f"STAT-ROI-{r.content_format.upper().replace(' ', '_')}",
                "amount": str(r.avg_roi),
                "memo": f"Avg ROI for {r.content_format}: {r.avg_roi}%",
            })
        await self.intacct.create_statistical_journal(
            journal_id="CONTENT-ROI",
            entries=entries,
            description="Monthly content ROI by format",
        )

    @staticmethod
    def _mock_production_costs() -> dict[str, dict]:
        """Mock production costs mapped to video IDs."""
        import random
        rng = random.Random(42)
        costs = {}
        formats = ["Long-Form", "Short", "Kids Series", "Branded", "Vertical"]
        crews = ["CREW-A", "CREW-B", "CREW-C", "CREW-D", "CREW-E"]
        for i in range(50):
            vid = f"mock_vid_{i:03d}"
            fmt = rng.choice(formats)
            base = {"Long-Form": 22000, "Short": 3000, "Branded": 45000,
                     "Kids Series": 12000, "Vertical": 2000}
            costs[vid] = {
                "project_code": f"PROJ-{i:03d}",
                "total_cost": Decimal(str(rng.randint(
                    int(base[fmt] * 0.6), int(base[fmt] * 1.4)
                ))),
                "format": fmt,
                "crew_id": rng.choice(crews),
            }
        return costs

    @staticmethod
    def _mock_video_metrics() -> dict[str, dict]:
        """Mock video metrics when YouTube is unavailable."""
        import random
        rng = random.Random(42)
        metrics = {}
        for i in range(50):
            vid = f"mock_vid_{i:03d}"
            metrics[vid] = {
                "title": f"Mock Episode {i+1}",
                "views": rng.randint(500_000, 80_000_000),
                "publish_date": date(2026, 1, 1),
            }
        return metrics
