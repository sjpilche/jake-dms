"""YouTube Data API v3 client — public data only (API key, no OAuth).

Fetches channel stats, recent videos, and per-video metrics for
Dhar Mann Studios. Caches every response to disk so the demo
works offline.
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import httpx
from loguru import logger

from src.core.config import get_settings
from src.core.models import YouTubeChannel, YouTubeVideo

BASE_URL = "https://www.googleapis.com/youtube/v3"
DEFAULT_CPM = Decimal("4.50")  # USD per 1,000 views


class YouTubePublicClient:
    """Thin wrapper around YouTube Data API v3 with disk caching."""

    def __init__(self, api_key: str | None = None, cache_dir: Path | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        self.cache_dir = cache_dir or settings.DATA_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.channel_id = settings.YOUTUBE_CHANNEL_ID
        self._client = httpx.Client(timeout=15)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_channel_stats(self) -> YouTubeChannel:
        """Fetch channel-level statistics."""
        data = self._api_call_cached(
            "channels",
            {"part": "snippet,statistics", "id": self.channel_id},
            "channel_stats",
        )
        item = data["items"][0]
        stats = item["statistics"]
        snippet = item["snippet"]
        return YouTubeChannel(
            channel_id=self.channel_id,
            title=snippet.get("title", ""),
            subscriber_count=int(stats.get("subscriberCount", 0)),
            view_count=int(stats.get("viewCount", 0)),
            video_count=int(stats.get("videoCount", 0)),
            thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        )

    def get_recent_videos(self, max_results: int = 50) -> list[YouTubeVideo]:
        """Fetch recent videos with full statistics."""
        # Step 1: search for recent video IDs
        search_data = self._api_call_cached(
            "search",
            {
                "part": "snippet",
                "channelId": self.channel_id,
                "order": "date",
                "type": "video",
                "maxResults": min(max_results, 50),
            },
            "recent_search",
        )
        video_ids = [
            item["id"]["videoId"]
            for item in search_data.get("items", [])
            if item.get("id", {}).get("videoId")
        ]
        if not video_ids:
            return []

        # Step 2: get full video details
        return self.get_video_details(video_ids)

    def get_video_details(self, video_ids: list[str]) -> list[YouTubeVideo]:
        """Fetch detailed stats for a list of video IDs."""
        # YouTube API accepts max 50 IDs per request
        all_videos: list[YouTubeVideo] = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i : i + 50]
            ids_str = ",".join(batch)
            data = self._api_call_cached(
                "videos",
                {"part": "snippet,statistics,contentDetails", "id": ids_str},
                f"video_details_{i}",
            )
            for item in data.get("items", []):
                all_videos.append(self._parse_video(item))
        return all_videos

    # ------------------------------------------------------------------
    # Revenue Estimation
    # ------------------------------------------------------------------

    @staticmethod
    def estimate_revenue(views: int, cpm: Decimal = DEFAULT_CPM) -> Decimal:
        """Deterministic CPM-based revenue estimate."""
        return Decimal(str(round(views * float(cpm) / 1000, 2)))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _api_call_cached(
        self, endpoint: str, params: dict, cache_key: str
    ) -> dict:
        """Make API call with disk caching fallback."""
        cache_file = self.cache_dir / f"youtube_cache_{cache_key}.json"

        # Try live API first
        if self.api_key:
            try:
                params["key"] = self.api_key
                resp = self._client.get(f"{BASE_URL}/{endpoint}", params=params)
                resp.raise_for_status()
                data = resp.json()

                # Cache the response
                cache_file.write_text(json.dumps(data, indent=2))
                logger.debug(f"YouTube API: fetched {endpoint}, cached to {cache_file.name}")
                return data
            except (httpx.HTTPError, KeyError) as e:
                logger.warning(f"YouTube API call failed ({e}), falling back to cache")

        # Fall back to cache
        if cache_file.exists():
            logger.info(f"Loading cached YouTube data from {cache_file.name}")
            return json.loads(cache_file.read_text())

        logger.error(f"No API key and no cache for {cache_key}")
        return {"items": []}

    @staticmethod
    def _parse_video(item: dict) -> YouTubeVideo:
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        content = item.get("contentDetails", {})

        # Parse ISO 8601 duration (PT#H#M#S)
        duration_str = content.get("duration", "PT0S")
        duration_seconds = _parse_iso_duration(duration_str)

        published = snippet.get("publishedAt", "2024-01-01T00:00:00Z")
        try:
            pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError:
            pub_dt = datetime(2024, 1, 1)

        return YouTubeVideo(
            video_id=item.get("id", ""),
            title=snippet.get("title", ""),
            published_at=pub_dt,
            view_count=int(stats.get("viewCount", 0)),
            like_count=int(stats.get("likeCount", 0)),
            comment_count=int(stats.get("commentCount", 0)),
            duration_seconds=duration_seconds,
            thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        )


def _parse_iso_duration(duration: str) -> int:
    """Parse ISO 8601 duration (e.g. PT1H2M3S) to total seconds."""
    import re

    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds
