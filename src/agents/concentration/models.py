"""Models for Revenue Concentration Monitor agent."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ConcentrationMetrics(BaseModel):
    model_config = ConfigDict(strict=True)
    period: str  # YYYY-MM or "YTD"
    platform_revenue_pct: Decimal
    non_platform_revenue_pct: Decimal
    herfindahl_index: Decimal  # 0-10000 (10000 = single source)
    largest_source: str
    largest_source_pct: Decimal
    revenue_by_source: dict[str, Decimal]
    alert_level: str  # GREEN | YELLOW | RED


class ConcentrationAlert(BaseModel):
    model_config = ConfigDict(strict=True)
    level: str  # RED | YELLOW | GREEN
    metric: str
    value: Decimal
    threshold: Decimal
    message: str
