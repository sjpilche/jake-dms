"""Pydantic v2 domain models — shared across all layers."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class BusinessLine(str, Enum):
    CORE_CONTENT = "Core Content"
    FIFTH_QUARTER = "5th Quarter"
    BRAND_DEALS = "Brand Deals"
    LICENSING = "Licensing/OTT"
    MERCHANDISE = "Merchandise"
    OTHER = "Other"


class Platform(str, Enum):
    YOUTUBE = "YouTube"
    FACEBOOK = "Facebook"
    TIKTOK = "TikTok"
    SNAP = "Snap"
    LICENSING = "Licensing"
    OTHER = "Other"


class ContentFormat(str, Enum):
    LONG_FORM = "Long-Form"
    SHORT = "Short"
    KIDS = "Kids Series"
    BRANDED = "Branded"
    VERTICAL = "Vertical"


class AgingBucket(str, Enum):
    CURRENT = "Current"
    DAYS_30 = "1-30 Days"
    DAYS_60 = "31-60 Days"
    DAYS_90 = "61-90 Days"
    DAYS_90_PLUS = "90+ Days"


# ---------------------------------------------------------------------------
# Financial Models
# ---------------------------------------------------------------------------

class GLAccount(BaseModel):
    model_config = ConfigDict(strict=True)

    account_no: str
    name: str
    category: str  # Revenue, Expense, Asset, Liability, Equity
    subcategory: str


class GLBalance(BaseModel):
    model_config = ConfigDict(strict=True)

    account_no: str
    period: str  # YYYY-MM
    debit: Decimal
    credit: Decimal
    net_balance: Decimal


class ARAgingRecord(BaseModel):
    model_config = ConfigDict(strict=True)

    customer: str
    current_amt: Decimal
    days_30: Decimal
    days_60: Decimal
    days_90_plus: Decimal
    total: Decimal
    as_of_date: date


class CashPosition(BaseModel):
    model_config = ConfigDict(strict=True)

    account_name: str
    bank_name: str
    balance: Decimal
    as_of_date: date


class ProductionCost(BaseModel):
    model_config = ConfigDict(strict=True)

    video_id: str
    video_title: str
    content_format: ContentFormat
    crew_id: str
    talent: Decimal
    crew_cost: Decimal
    location: Decimal
    post_production: Decimal
    music_licensing: Decimal
    total_cost: Decimal
    production_date: date


class PlatformRevenue(BaseModel):
    model_config = ConfigDict(strict=True)

    platform: Platform
    business_line: BusinessLine
    period: str  # YYYY-MM
    ad_revenue: Decimal
    sponsorship_revenue: Decimal
    licensing_revenue: Decimal
    total_revenue: Decimal


class PLLineItem(BaseModel):
    model_config = ConfigDict(strict=True)

    category: str  # Revenue, COGS, OpEx, etc.
    subcategory: str
    business_line: BusinessLine
    period: str  # YYYY-MM
    amount: Decimal


# ---------------------------------------------------------------------------
# YouTube Models
# ---------------------------------------------------------------------------

class YouTubeChannel(BaseModel):
    model_config = ConfigDict(strict=True)

    channel_id: str
    title: str
    subscriber_count: int
    view_count: int
    video_count: int
    thumbnail_url: str


class YouTubeVideo(BaseModel):
    model_config = ConfigDict(strict=True)

    video_id: str
    title: str
    published_at: datetime
    view_count: int
    like_count: int
    comment_count: int
    duration_seconds: int
    thumbnail_url: str


# ---------------------------------------------------------------------------
# Derived / Composite Models
# ---------------------------------------------------------------------------

class ContentROI(BaseModel):
    model_config = ConfigDict(strict=True)

    video_id: str
    title: str
    content_format: ContentFormat
    production_cost: Decimal
    estimated_revenue: Decimal
    views: int
    cost_per_view: Decimal
    cost_per_1k_views: Decimal
    margin: Decimal  # (revenue - cost) / revenue
    roi: Decimal  # revenue / cost


class CashFlowWeek(BaseModel):
    model_config = ConfigDict(strict=True)

    week_number: int
    week_start: date
    opening_cash: Decimal
    platform_inflows: Decimal
    brand_deal_inflows: Decimal
    other_inflows: Decimal
    total_inflows: Decimal
    payroll_outflows: Decimal
    production_outflows: Decimal
    facility_outflows: Decimal
    other_outflows: Decimal
    total_outflows: Decimal
    net_change: Decimal
    closing_cash: Decimal
    below_minimum: bool


class ReconRecord(BaseModel):
    model_config = ConfigDict(strict=True)

    platform: Platform
    period: str  # YYYY-MM
    estimated_revenue: Decimal
    actual_received: Decimal
    variance: Decimal
    variance_pct: Decimal
    status: str  # Matched, Flagged, Pending
