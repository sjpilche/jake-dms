"""SQLAlchemy ORM models for the Jake-DMS demo database."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class GLAccountRow(Base):
    __tablename__ = "gl_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    subcategory: Mapped[str] = mapped_column(String(100), nullable=False)


class GLBalanceRow(Base):
    __tablename__ = "gl_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_no: Mapped[str] = mapped_column(String(20), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    debit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    credit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    net_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)


class ARAgingRow(Base):
    __tablename__ = "ar_aging"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer: Mapped[str] = mapped_column(String(200), nullable=False)
    current_amt: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    days_30: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    days_60: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    days_90_plus: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)


class APAgingRow(Base):
    __tablename__ = "ap_aging"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor: Mapped[str] = mapped_column(String(200), nullable=False)
    current_amt: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    days_30: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    days_60: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    days_90_plus: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)


class CashBalanceRow(Base):
    __tablename__ = "cash_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)


class ProductionCostRow(Base):
    __tablename__ = "production_costs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[str] = mapped_column(String(20), nullable=False)
    video_title: Mapped[str] = mapped_column(Text, nullable=False)
    content_format: Mapped[str] = mapped_column(String(20), nullable=False)
    crew_id: Mapped[str] = mapped_column(String(20), nullable=False)
    talent: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    crew_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    location: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    post_production: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    music_licensing: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    production_date: Mapped[date] = mapped_column(Date, nullable=False)


class PlatformRevenueRow(Base):
    __tablename__ = "platform_revenue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(30), nullable=False)
    business_line: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    ad_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    sponsorship_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    licensing_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)


class PLRow(Base):
    __tablename__ = "pl_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    subcategory: Mapped[str] = mapped_column(String(100), nullable=False)
    business_line: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)


class ReconRecordRow(Base):
    __tablename__ = "recon_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(30), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    estimated_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    actual_received: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    variance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    variance_pct: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
