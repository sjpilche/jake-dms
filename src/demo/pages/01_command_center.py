"""Page 1: Command Center — Executive financial overview."""

from __future__ import annotations

import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import func, text

from src.db.engine import get_session
from src.db.models import (
    ARAgingRow,
    CashBalanceRow,
    PlatformRevenueRow,
    PLRow,
)
from src.demo.mock_data import ensure_demo_data
from src.demo.theme import (
    BIZ_LINE_COLORS,
    CHART_COLORS,
    PLATFORM_COLORS,
    TEAL,
    format_currency,
    format_number,
    kpi_row,
    page_config,
    page_header,
    render_sidebar,
)
from src.demo.youtube_public import YouTubePublicClient

page_config("Command Center | DMS CFO")
ensure_demo_data()
render_sidebar()
page_header("Command Center", "Executive Financial Overview")


# ---------------------------------------------------------------------------
# Cached Data Loading
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def load_revenue_by_period() -> dict[str, float]:
    session = get_session()
    rows = (
        session.query(PLRow.period, func.sum(PLRow.amount).label("total"))
        .filter(PLRow.category == "Revenue")
        .group_by(PLRow.period).order_by(PLRow.period).all()
    )
    session.close()
    return {r.period: float(r.total) for r in rows}


@st.cache_data(ttl=300)
def load_expenses_by_period() -> dict[str, float]:
    session = get_session()
    rows = (
        session.query(PLRow.period, func.sum(PLRow.amount).label("total"))
        .filter(PLRow.category.in_(["COGS", "OpEx"]))
        .group_by(PLRow.period).order_by(PLRow.period).all()
    )
    session.close()
    return {r.period: float(r.total) for r in rows}


@st.cache_data(ttl=300)
def load_cash_total() -> float:
    session = get_session()
    rows = session.query(CashBalanceRow).all()
    session.close()
    return sum(float(r.balance) for r in rows)


@st.cache_data(ttl=3600)
def load_subscriber_count() -> int:
    try:
        yt = YouTubePublicClient()
        return yt.get_channel_stats().subscriber_count
    except Exception:
        return 20_600_000


@st.cache_data(ttl=300)
def load_platform_revenue() -> tuple[list[str], list[float]]:
    session = get_session()
    rows = (
        session.query(
            PlatformRevenueRow.platform,
            func.sum(PlatformRevenueRow.total_revenue).label("total"),
        )
        .group_by(PlatformRevenueRow.platform)
        .order_by(text("total DESC")).all()
    )
    session.close()
    return [r.platform for r in rows], [float(r.total) for r in rows]


@st.cache_data(ttl=300)
def load_ar_aging() -> pd.DataFrame:
    session = get_session()
    rows = session.query(ARAgingRow).all()
    session.close()
    return pd.DataFrame([
        {
            "Customer": r.customer, "Current": float(r.current_amt),
            "1-30 Days": float(r.days_30), "31-60 Days": float(r.days_60),
            "90+ Days": float(r.days_90_plus), "Total": float(r.total),
        }
        for r in rows
    ]).sort_values("Total", ascending=False)


@st.cache_data(ttl=300)
def load_biz_line_revenue() -> tuple[list[str], list[float]]:
    session = get_session()
    rows = (
        session.query(PLRow.business_line, func.sum(PLRow.amount).label("total"))
        .filter(PLRow.category == "Revenue")
        .group_by(PLRow.business_line).order_by(text("total DESC")).all()
    )
    session.close()
    return [r.business_line for r in rows], [float(r.total) for r in rows]


# ---------------------------------------------------------------------------
# Load all data (cached)
# ---------------------------------------------------------------------------

rev_by_period = load_revenue_by_period()
exp_by_period = load_expenses_by_period()
ttm_revenue = sum(list(rev_by_period.values())[-12:])
ttm_expenses = sum(list(exp_by_period.values())[-12:])
op_margin = ((ttm_revenue - ttm_expenses) / ttm_revenue * 100) if ttm_revenue else 0
total_cash = load_cash_total()
subscriber_count = load_subscriber_count()

# ---------------------------------------------------------------------------
# KPI Row
# ---------------------------------------------------------------------------

kpi_row([
    {"label": "TTM Revenue", "value": format_currency(ttm_revenue), "delta": "+12% YoY"},
    {"label": "Operating Margin", "value": f"{op_margin:.1f}%", "delta": "+2.3pp"},
    {"label": "Cash Position", "value": format_currency(total_cash), "delta": None},
    {"label": "YouTube Subscribers", "value": format_number(subscriber_count), "delta": "+1.2M YoY"},
])

st.markdown("---")

# ---------------------------------------------------------------------------
# Revenue Trend + Platform Mix
# ---------------------------------------------------------------------------

col_chart1, col_chart2 = st.columns([3, 2])

with col_chart1:
    st.subheader("Monthly Revenue Trend")
    periods = sorted(rev_by_period.keys())
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=periods, y=[rev_by_period[p] for p in periods],
        mode="lines+markers", line={"color": TEAL, "width": 3},
        marker={"size": 6}, name="Revenue",
    ))
    fig_trend.add_trace(go.Scatter(
        x=periods, y=[exp_by_period.get(p, 0) for p in periods],
        mode="lines", line={"color": "#E63946", "width": 2, "dash": "dot"},
        name="Expenses",
    ))
    fig_trend.update_layout(
        height=350, margin={"l": 40, "r": 20, "t": 30, "b": 40},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis_tickprefix="$", yaxis_tickformat=",",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        xaxis={"showgrid": False},
        yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.1)"},
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_chart2:
    st.subheader("Revenue by Platform")
    plat_labels, plat_values = load_platform_revenue()
    plat_colors = [PLATFORM_COLORS.get(l, "#999") for l in plat_labels]
    fig_donut = go.Figure(data=[go.Pie(
        labels=plat_labels, values=plat_values, hole=0.5,
        marker={"colors": plat_colors}, textinfo="label+percent",
        textposition="outside",
    )])
    fig_donut.update_layout(
        height=350, margin={"l": 10, "r": 10, "t": 30, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# ---------------------------------------------------------------------------
# AR Aging + Revenue by Business Line
# ---------------------------------------------------------------------------

col_ar, col_biz = st.columns(2)

with col_ar:
    st.subheader("AR Aging Summary")
    ar_df = load_ar_aging()
    if not ar_df.empty:
        fig_ar = go.Figure()
        for i, bucket in enumerate(["Current", "1-30 Days", "31-60 Days", "90+ Days"]):
            colors = [TEAL, CHART_COLORS[1], CHART_COLORS[4], "#E63946"]
            fig_ar.add_trace(go.Bar(
                x=ar_df["Customer"], y=ar_df[bucket],
                name=bucket, marker_color=colors[i],
            ))
        fig_ar.update_layout(
            barmode="stack", height=350,
            margin={"l": 40, "r": 20, "t": 10, "b": 100},
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis_tickprefix="$", yaxis_tickformat=",", xaxis_tickangle=-45,
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
            yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.1)"},
        )
        st.plotly_chart(fig_ar, use_container_width=True)

with col_biz:
    st.subheader("Revenue by Business Line (TTM)")
    biz_labels, biz_values = load_biz_line_revenue()
    biz_colors = [BIZ_LINE_COLORS.get(l, "#999") for l in biz_labels]
    fig_biz = go.Figure(data=[go.Bar(
        x=biz_labels, y=biz_values, marker_color=biz_colors,
    )])
    fig_biz.update_layout(
        height=350, margin={"l": 40, "r": 20, "t": 10, "b": 40},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis_tickprefix="$", yaxis_tickformat=",",
        yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.1)"},
    )
    st.plotly_chart(fig_biz, use_container_width=True)

# ---------------------------------------------------------------------------
# Agent Status Panel
# ---------------------------------------------------------------------------

st.subheader("Agent Status")
agents = [
    ("Platform Revenue Intelligence", "Active", "Monitoring YouTube + Meta daily revenue"),
    ("Content ROI Engine", "Active", "Tracking 50 episodes, weekly ROI reports"),
    ("Cash & Treasury", "Active", "13-week forecast updated daily"),
    ("Revenue Concentration Monitor", "Active", "Platform mix at 51% — watch zone"),
    ("Deal & Revenue Recognition", "Standby", "Awaiting Intacct Contracts module"),
    ("Investor Reporting", "Standby", "Monthly close package on demand"),
]
agent_df = pd.DataFrame(agents, columns=["Agent Domain", "Status", "Latest Activity"])
st.dataframe(agent_df, use_container_width=True, hide_index=True,
             column_config={"Status": st.column_config.TextColumn(width="small")})
