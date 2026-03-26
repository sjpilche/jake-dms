"""YouTube Analytics API client — OAuth2 for actual revenue data.

Unlike the public Data API v3 client (demo), this uses OAuth2 to access
the YouTube Analytics API which provides actual revenue metrics:
estimatedRevenue, CPM, adRevenue, etc.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import httpx
from loguru import logger
from pydantic import BaseModel, ConfigDict

from src.core.config import get_settings

ANALYTICS_BASE = "https://youtubeanalytics.googleapis.com/v2/reports"


class DailyMetrics(BaseModel):
    model_config = ConfigDict(strict=True)
    date: date
    views: int
    estimated_revenue: Decimal
    estimated_ad_revenue: Decimal
    cpm: Decimal
    average_view_duration: int
    subscribers_gained: int


class GeoRevenue(BaseModel):
    model_config = ConfigDict(strict=True)
    country: str
    views: int
    estimated_revenue: Decimal
    cpm: Decimal


class YouTubeAnalyticsClient:
    """OAuth2 client for YouTube Analytics API — actual revenue data."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = httpx.AsyncClient(timeout=15)
        self._access_token: str | None = None

    async def close(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    async def _get_token(self) -> str:
        """Load OAuth2 access token from stored credentials."""
        if self._access_token:
            return self._access_token

        token_path = Path(self.settings.YOUTUBE_OAUTH_TOKEN_PATH)
        if not token_path.exists():
            raise RuntimeError(
                f"YouTube OAuth token not found at {token_path}. "
                "Run the OAuth flow first: python -m src.core.youtube_analytics --auth"
            )

        token_data = json.loads(token_path.read_text())
        self._access_token = token_data["access_token"]

        # Check if token needs refresh
        if token_data.get("refresh_token"):
            try:
                refreshed = await self._refresh_token(
                    token_data["refresh_token"],
                    self.settings.YOUTUBE_OAUTH_CLIENT_ID,
                    self.settings.YOUTUBE_OAUTH_CLIENT_SECRET,
                )
                self._access_token = refreshed
                token_data["access_token"] = refreshed
                token_path.write_text(json.dumps(token_data, indent=2))
            except Exception as e:
                logger.warning(f"Token refresh failed, using existing: {e}")

        return self._access_token

    async def _refresh_token(
        self, refresh_token: str, client_id: str, client_secret: str
    ) -> str:
        resp = await self._client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    async def _headers(self) -> dict[str, str]:
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}"}

    # ------------------------------------------------------------------
    # Revenue Metrics
    # ------------------------------------------------------------------

    async def get_daily_metrics(
        self, start: date, end: date
    ) -> list[DailyMetrics]:
        """Pull daily views, estimated revenue, CPM, watch time."""
        if self.settings.DEMO_MODE:
            return self._mock_daily_metrics(start, end)

        params = {
            "ids": f"channel=={self.settings.YOUTUBE_CHANNEL_ID}",
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "metrics": "views,estimatedRevenue,estimatedAdRevenue,cpm,"
                       "averageViewDuration,subscribersGained",
            "dimensions": "day",
            "sort": "day",
        }
        resp = await self._client.get(
            ANALYTICS_BASE, params=params, headers=await self._headers()
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for row in data.get("rows", []):
            results.append(DailyMetrics(
                date=date.fromisoformat(row[0]),
                views=int(row[1]),
                estimated_revenue=Decimal(str(row[2])),
                estimated_ad_revenue=Decimal(str(row[3])),
                cpm=Decimal(str(row[4])),
                average_view_duration=int(row[5]),
                subscribers_gained=int(row[6]),
            ))
        return results

    async def get_geo_breakdown(
        self, start: date, end: date, max_results: int = 25
    ) -> list[GeoRevenue]:
        """Revenue by country for CPM geo-weighting."""
        if self.settings.DEMO_MODE:
            return self._mock_geo_breakdown()

        params = {
            "ids": f"channel=={self.settings.YOUTUBE_CHANNEL_ID}",
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "metrics": "views,estimatedRevenue,cpm",
            "dimensions": "country",
            "sort": "-estimatedRevenue",
            "maxResults": max_results,
        }
        resp = await self._client.get(
            ANALYTICS_BASE, params=params, headers=await self._headers()
        )
        resp.raise_for_status()
        data = resp.json()

        return [
            GeoRevenue(
                country=row[0], views=int(row[1]),
                estimated_revenue=Decimal(str(row[2])),
                cpm=Decimal(str(row[3])),
            )
            for row in data.get("rows", [])
        ]

    async def get_monthly_revenue(self, year: int, month: int) -> Decimal:
        """Get total estimated revenue for a given month."""
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)
        from datetime import timedelta
        end = end - timedelta(days=1)

        metrics = await self.get_daily_metrics(start, end)
        return sum((m.estimated_revenue for m in metrics), Decimal("0"))

    # ------------------------------------------------------------------
    # Mock Data
    # ------------------------------------------------------------------

    @staticmethod
    def _mock_daily_metrics(start: date, end: date) -> list[DailyMetrics]:
        import random
        rng = random.Random(42)
        results = []
        current = start
        while current <= end:
            results.append(DailyMetrics(
                date=current,
                views=rng.randint(5_000_000, 15_000_000),
                estimated_revenue=Decimal(str(round(rng.uniform(20_000, 60_000), 2))),
                estimated_ad_revenue=Decimal(str(round(rng.uniform(18_000, 55_000), 2))),
                cpm=Decimal(str(round(rng.uniform(3.5, 6.0), 2))),
                average_view_duration=rng.randint(180, 420),
                subscribers_gained=rng.randint(5_000, 25_000),
            ))
            from datetime import timedelta
            current += timedelta(days=1)
        return results

    @staticmethod
    def _mock_geo_breakdown() -> list[GeoRevenue]:
        return [
            GeoRevenue(country="US", views=50_000_000, estimated_revenue=Decimal("280000"), cpm=Decimal("5.60")),
            GeoRevenue(country="GB", views=8_000_000, estimated_revenue=Decimal("36000"), cpm=Decimal("4.50")),
            GeoRevenue(country="CA", views=6_000_000, estimated_revenue=Decimal("27000"), cpm=Decimal("4.50")),
            GeoRevenue(country="AU", views=4_000_000, estimated_revenue=Decimal("18000"), cpm=Decimal("4.50")),
            GeoRevenue(country="IN", views=20_000_000, estimated_revenue=Decimal("14000"), cpm=Decimal("0.70")),
            GeoRevenue(country="PH", views=12_000_000, estimated_revenue=Decimal("7200"), cpm=Decimal("0.60")),
            GeoRevenue(country="DE", views=3_000_000, estimated_revenue=Decimal("12000"), cpm=Decimal("4.00")),
        ]
