"""Page 5: Investor Package — Board-ready metrics summary."""

from __future__ import annotations

import io

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
    PLATFORM_COLORS,
    format_currency,
    kpi_row,
    page_config,
    page_header,
    render_sidebar,
)
from src.demo.youtube_public import YouTubePublicClient

page_config("Investor Package | DMS CFO")
ensure_demo_data()
render_sidebar()
page_header("Investor Package", "Monthly Board & Investor Metrics Summary")


# ---------------------------------------------------------------------------
# Cached Data Loading
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def load_pl_summary() -> tuple[float, float, float, list[tuple[str, str, float]]]:
    session = get_session()
    rows = (
        session.query(PLRow.category, PLRow.subcategory, func.sum(PLRow.amount).label("total"))
        .group_by(PLRow.category, PLRow.subcategory).all()
    )
    session.close()
    details = [(r.category, r.subcategory, float(r.total)) for r in rows]
    rev = sum(v for c, _, v in details if c == "Revenue")
    cogs = sum(v for c, _, v in details if c == "COGS")
    opex = sum(v for c, _, v in details if c == "OpEx")
    return rev, cogs, opex, details


@st.cache_data(ttl=300)
def load_platform_concentration() -> tuple[dict[str, float], float]:
    session = get_session()
    rows = (
        session.query(PlatformRevenueRow.platform,
                      func.sum(PlatformRevenueRow.total_revenue).label("total"))
        .group_by(PlatformRevenueRow.platform).all()
    )
    session.close()
    total = sum(float(r.total) for r in rows)
    pct = {r.platform: float(r.total) / total * 100 for r in rows} if total else {}
    return pct, total


@st.cache_data(ttl=300)
def load_cash_and_ar() -> tuple[float, float]:
    session = get_session()
    cash = sum(float(r.balance) for r in session.query(CashBalanceRow).all())
    ar = sum(float(r.total) for r in session.query(ARAgingRow).all())
    session.close()
    return cash, ar


@st.cache_data(ttl=300)
def load_revenue_by_biz_period() -> pd.DataFrame:
    session = get_session()
    rows = (
        session.query(PLRow.business_line, PLRow.period, func.sum(PLRow.amount).label("total"))
        .filter(PLRow.category == "Revenue")
        .group_by(PLRow.business_line, PLRow.period).order_by(PLRow.period).all()
    )
    session.close()
    return pd.DataFrame([
        {"Business Line": r.business_line, "Period": r.period, "Revenue": float(r.total)}
        for r in rows
    ])


@st.cache_data(ttl=3600)
def load_yt_channel() -> dict | None:
    try:
        yt = YouTubePublicClient()
        ch = yt.get_channel_stats()
        return {"subscribers": ch.subscriber_count, "views": ch.view_count, "videos": ch.video_count}
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

total_revenue, total_cogs, total_opex, pl_details = load_pl_summary()
gross_profit = total_revenue - total_cogs
gross_margin = (gross_profit / total_revenue * 100) if total_revenue else 0
op_margin = ((total_revenue - total_cogs - total_opex) / total_revenue * 100) if total_revenue else 0

platform_pct, _ = load_platform_concentration()
yt_pct = platform_pct.get("YouTube", 0)
fb_pct = platform_pct.get("Facebook", 0)
platform_concentration = yt_pct + fb_pct

total_cash, total_ar = load_cash_and_ar()

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------

kpi_row([
    {"label": "Total Revenue (18mo)", "value": format_currency(total_revenue)},
    {"label": "Gross Margin", "value": f"{gross_margin:.1f}%"},
    {"label": "Operating Margin", "value": f"{op_margin:.1f}%"},
    {
        "label": "Platform Concentration",
        "value": f"{platform_concentration:.0f}%",
        "delta": "Target: <40%",
        "delta_color": "inverse" if platform_concentration > 50 else "normal",
    },
])

st.markdown("---")

# ---------------------------------------------------------------------------
# P&L + Diversification
# ---------------------------------------------------------------------------

col_pl, col_mix = st.columns([3, 2])

with col_pl:
    st.subheader("Profit & Loss Summary")
    pl_data = [
        {"Line Item": "Revenue", "Amount": total_revenue, "% of Revenue": "100.0%"},
        {"Line Item": "Cost of Goods Sold", "Amount": -total_cogs, "% of Revenue": f"{total_cogs/total_revenue*100:.1f}%"},
        {"Line Item": "**Gross Profit**", "Amount": gross_profit, "% of Revenue": f"{gross_margin:.1f}%"},
        {"Line Item": "Operating Expenses", "Amount": -total_opex, "% of Revenue": f"{total_opex/total_revenue*100:.1f}%"},
        {"Line Item": "**Operating Income**", "Amount": total_revenue - total_cogs - total_opex, "% of Revenue": f"{op_margin:.1f}%"},
    ]
    st.dataframe(pd.DataFrame(pl_data), use_container_width=True, hide_index=True,
                 column_config={"Amount": st.column_config.NumberColumn(format="$%,.0f")})

    st.caption("**COGS Breakdown**")
    cogs_items = [(s, v) for c, s, v in pl_details if c == "COGS"]
    st.dataframe(pd.DataFrame(cogs_items, columns=["Category", "Amount"]).sort_values("Amount", ascending=False),
                 use_container_width=True, hide_index=True,
                 column_config={"Amount": st.column_config.NumberColumn(format="$%,.0f")})

    st.caption("**Operating Expense Breakdown**")
    opex_items = [(s, v) for c, s, v in pl_details if c == "OpEx"]
    st.dataframe(pd.DataFrame(opex_items, columns=["Category", "Amount"]).sort_values("Amount", ascending=False),
                 use_container_width=True, hide_index=True,
                 column_config={"Amount": st.column_config.NumberColumn(format="$%,.0f")})

with col_mix:
    st.subheader("Revenue Diversification")
    plat_labels = list(platform_pct.keys())
    plat_values = list(platform_pct.values())
    plat_colors = [PLATFORM_COLORS.get(l, "#999") for l in plat_labels]
    fig_mix = go.Figure(data=[go.Pie(
        labels=plat_labels, values=plat_values, hole=0.5,
        marker={"colors": plat_colors}, textinfo="label+percent", textposition="outside",
    )])
    fig_mix.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                          margin={"l": 10, "r": 10, "t": 10, "b": 10})
    st.plotly_chart(fig_mix, use_container_width=True)

    if platform_concentration > 50:
        st.error(f"Platform concentration at {platform_concentration:.0f}% — above the 40% target. YouTube alone is {yt_pct:.0f}%.")
    elif platform_concentration > 40:
        st.warning(f"Platform concentration at {platform_concentration:.0f}% — near the 40% target.")
    else:
        st.success(f"Platform concentration at {platform_concentration:.0f}% — below the 40% target.")

    st.subheader("Key Ratios")
    for label, value in {
        "Gross Margin": f"{gross_margin:.1f}%",
        "Operating Margin": f"{op_margin:.1f}%",
        "Cash Position": format_currency(total_cash),
        "Total AR": format_currency(total_ar),
        "Revenue/Employee (est.)": format_currency(total_revenue / 18 * 12 / 200),
        "Largest Single Source": f"YouTube ({yt_pct:.0f}%)",
    }.items():
        st.markdown(f"**{label}:** {value}")

# ---------------------------------------------------------------------------
# Revenue by Business Line Over Time
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Revenue by Business Line — Monthly Trend")
biz_df = load_revenue_by_biz_period()
if not biz_df.empty:
    pivot = biz_df.pivot_table(index="Period", columns="Business Line", values="Revenue", aggfunc="sum").fillna(0).sort_index()
    fig_trend = go.Figure()
    for biz in pivot.columns:
        fig_trend.add_trace(go.Bar(x=pivot.index, y=pivot[biz], name=biz,
                                   marker_color=BIZ_LINE_COLORS.get(biz, "#999")))
    fig_trend.update_layout(
        barmode="stack", height=400,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis_tickprefix="$", yaxis_tickformat=",",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        margin={"l": 60, "r": 20, "t": 30, "b": 40},
        xaxis={"showgrid": False}, yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.1)"},
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# ---------------------------------------------------------------------------
# YouTube Growth
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("YouTube Channel Metrics")
yt_data = load_yt_channel()
if yt_data:
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Subscribers", f"{yt_data['subscribers']:,}")
    with c2: st.metric("Total Views", f"{yt_data['views']:,}")
    with c3: st.metric("Total Videos", f"{yt_data['videos']:,}")
else:
    st.info("YouTube data unavailable — add YOUTUBE_API_KEY to .env for live metrics")

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Export Data")
export_df = pd.DataFrame({
    "Metric": ["Total Revenue (18mo)", "Gross Profit", "Operating Income",
               "Gross Margin", "Operating Margin", "Cash Position", "Total AR", "Platform Concentration"],
    "Value": [f"${total_revenue:,.0f}", f"${gross_profit:,.0f}",
              f"${total_revenue - total_cogs - total_opex:,.0f}",
              f"{gross_margin:.1f}%", f"{op_margin:.1f}%",
              f"${total_cash:,.0f}", f"${total_ar:,.0f}", f"{platform_concentration:.0f}%"],
})
csv_buf = io.StringIO()
export_df.to_csv(csv_buf, index=False)
st.download_button("Download Summary as CSV", csv_buf.getvalue(), "dms_investor_summary.csv", "text/csv")
