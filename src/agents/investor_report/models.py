"""Models for Investor Reporting agent."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class InvestorPackage(BaseModel):
    model_config = ConfigDict(strict=True)
    period: str  # YYYY-MM
    generated_at: date
    # P&L
    total_revenue: Decimal
    total_cogs: Decimal
    gross_profit: Decimal
    gross_margin_pct: Decimal
    total_opex: Decimal
    operating_income: Decimal
    operating_margin_pct: Decimal
    # Revenue mix
    revenue_by_business_line: dict[str, Decimal]
    revenue_by_platform: dict[str, Decimal]
    platform_concentration_pct: Decimal
    # Cash
    total_cash: Decimal
    total_ar: Decimal
    # Operating metrics
    youtube_subscribers: int
    youtube_total_views: int
    episodes_produced: int
    avg_cost_per_episode: Decimal
    avg_revenue_per_episode: Decimal


class ReportOutput(BaseModel):
    model_config = ConfigDict(strict=True)
    format: str  # "pdf" | "excel" | "csv"
    file_path: str
    size_bytes: int
