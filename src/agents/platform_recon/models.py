"""Models for Platform Revenue Reconciliation agent."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PlatformEstimate(BaseModel):
    model_config = ConfigDict(strict=True)
    platform: str
    period: str  # YYYY-MM
    estimated_revenue: Decimal
    source: str  # "youtube_analytics" | "meta_api" | "manual"


class GLDeposit(BaseModel):
    model_config = ConfigDict(strict=True)
    platform: str
    period: str
    actual_received: Decimal
    deposit_date: date
    reference: str


class ReconResult(BaseModel):
    model_config = ConfigDict(strict=True)
    platform: str
    period: str
    estimated_revenue: Decimal
    actual_received: Decimal
    variance: Decimal
    variance_pct: Decimal
    status: str  # Matched | Flagged | Pending
    explanation: str = ""
