"""Tests for the YouTube public data client."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from src.demo.youtube_public import YouTubePublicClient, _parse_iso_duration


def test_parse_iso_duration_full() -> None:
    assert _parse_iso_duration("PT1H2M3S") == 3723


def test_parse_iso_duration_minutes_only() -> None:
    assert _parse_iso_duration("PT15M30S") == 930


def test_parse_iso_duration_seconds_only() -> None:
    assert _parse_iso_duration("PT45S") == 45


def test_parse_iso_duration_hours_only() -> None:
    assert _parse_iso_duration("PT2H") == 7200


def test_parse_iso_duration_empty() -> None:
    assert _parse_iso_duration("PT0S") == 0


def test_parse_iso_duration_invalid() -> None:
    assert _parse_iso_duration("invalid") == 0


def test_estimate_revenue_default_cpm() -> None:
    result = YouTubePublicClient.estimate_revenue(1_000_000)
    assert result == Decimal("4500.00")


def test_estimate_revenue_custom_cpm() -> None:
    result = YouTubePublicClient.estimate_revenue(1_000_000, Decimal("3.50"))
    assert result == Decimal("3500.00")


def test_estimate_revenue_zero_views() -> None:
    result = YouTubePublicClient.estimate_revenue(0)
    assert result == Decimal("0.00")


def test_cache_fallback(tmp_path: Path) -> None:
    """Client should fall back to cached data when API key is empty."""
    # Write a mock cache file
    cache_data = {
        "items": [{
            "id": "UC_test",
            "snippet": {
                "title": "Test Channel",
                "thumbnails": {"high": {"url": "http://example.com/thumb.jpg"}},
            },
            "statistics": {
                "subscriberCount": "1000000",
                "viewCount": "500000000",
                "videoCount": "1500",
            },
        }]
    }
    cache_file = tmp_path / "youtube_cache_channel_stats.json"
    cache_file.write_text(json.dumps(cache_data))

    client = YouTubePublicClient(api_key="", cache_dir=tmp_path)
    channel = client.get_channel_stats()
    assert channel.subscriber_count == 1_000_000
    assert channel.title == "Test Channel"
