"""Models for Content ROI Engine agent."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class EpisodeMapping(BaseModel):
    model_config = ConfigDict(strict=True)
    project_code: str  # Intacct project code
    youtube_video_id: str
    title: str
    content_format: str
    series: str | None = None
    crew_id: str
    publish_date: date


class EpisodeROI(BaseModel):
    model_config = ConfigDict(strict=True)
    episode_id: str
    youtube_video_id: str
    title: str
    content_format: str
    series: str | None = None
    crew_id: str
    publish_date: date
    production_cost: Decimal
    lifetime_views: int
    lifetime_revenue: Decimal
    cost_per_view: Decimal
    cost_per_1k_views: Decimal
    revenue_per_episode: Decimal
    margin: Decimal  # (revenue - cost) / revenue
    roi: Decimal  # revenue / cost


class FormatMarginReport(BaseModel):
    model_config = ConfigDict(strict=True)
    content_format: str
    episode_count: int
    total_production_cost: Decimal
    total_revenue: Decimal
    avg_cost_per_episode: Decimal
    avg_revenue_per_episode: Decimal
    avg_roi: Decimal
    avg_cost_per_1k_views: Decimal
