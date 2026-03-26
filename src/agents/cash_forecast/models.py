"""Models for Cash Flow Forecast agent."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class WeeklyForecast(BaseModel):
    model_config = ConfigDict(strict=True)
    week_number: int
    week_start: date
    opening_cash: Decimal
    # Inflows
    platform_inflows: Decimal
    brand_deal_inflows: Decimal
    licensing_inflows: Decimal
    other_inflows: Decimal
    total_inflows: Decimal
    # Outflows
    payroll: Decimal
    production: Decimal
    talent: Decimal
    facilities: Decimal
    technology: Decimal
    marketing: Decimal
    ga: Decimal
    total_outflows: Decimal
    # Net
    net_change: Decimal
    closing_cash: Decimal
    below_minimum: bool


class CashAlert(BaseModel):
    model_config = ConfigDict(strict=True)
    alert_type: str  # "below_minimum" | "declining_trend" | "large_outflow"
    week_number: int
    projected_cash: Decimal
    threshold: Decimal
    message: str
