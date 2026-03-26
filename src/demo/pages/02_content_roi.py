"""Page 2: Content ROI — Episode-level profitability analysis."""

from __future__ import annotations

import random

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.db.engine import get_session
from src.db.models import ProductionCostRow
from src.demo.mock_data import ensure_demo_data
from src.demo.theme import (
    CHART_COLORS,
    TEAL,
    format_currency,
    kpi_row,
    page_config,
    page_header,
    render_sidebar,
)
from src.demo.youtube_public import YouTubePublicClient

page_config("Content ROI | DMS CFO")
ensure_demo_data()
render_sidebar()
page_header("Content ROI", "Episode-Level Profitability Analysis")


# ---------------------------------------------------------------------------
# Cached Data Loading
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def load_production_costs() -> list[dict]:
    session = get_session()
    rows = session.query(ProductionCostRow).all()
    session.close()
    return [
        {
            "video_id": r.video_id, "video_title": r.video_title,
            "content_format": r.content_format, "crew_id": r.crew_id,
            "total_cost": float(r.total_cost),
        }
        for r in rows
    ]


@st.cache_data(ttl=3600)
def load_youtube_videos() -> list[dict]:
    try:
        yt = YouTubePublicClient()
        videos = yt.get_recent_videos(max_results=50)
        return [
            {"video_id": v.video_id, "title": v.title, "view_count": v.view_count}
            for v in videos
        ]
    except Exception:
        return []


def build_roi_table(costs: list[dict], yt_videos: list[dict], cpm: float) -> pd.DataFrame:
    rng = random.Random(42)
    roi_data = []
    for i, cost in enumerate(costs):
        if i < len(yt_videos):
            views = yt_videos[i]["view_count"]
            title_display = yt_videos[i]["title"]
            video_id = yt_videos[i]["video_id"]
        else:
            views = rng.randint(500_000, 80_000_000)
            title_display = cost["video_title"]
            video_id = cost["video_id"]

        est_revenue = round(views * cpm / 1000, 2)
        prod_cost = cost["total_cost"]
        margin = ((est_revenue - prod_cost) / est_revenue * 100) if est_revenue > 0 else -100
        roi_pct = ((est_revenue - prod_cost) / prod_cost * 100) if prod_cost > 0 else 0
        cpv = prod_cost / views if views > 0 else 0

        roi_data.append({
            "Video ID": video_id, "Title": title_display,
            "Format": cost["content_format"], "Crew": cost["crew_id"],
            "Views": views, "Est. Revenue": est_revenue,
            "Production Cost": prod_cost, "Margin %": round(margin, 1),
            "ROI %": round(roi_pct, 1), "Cost/View": round(cpv, 4),
            "Cost/1K Views": round(cpv * 1000, 2),
        })
    return pd.DataFrame(roi_data)


# ---------------------------------------------------------------------------
# Load + Build
# ---------------------------------------------------------------------------

costs = load_production_costs()
yt_videos = load_youtube_videos()

cpm = st.sidebar.slider("CPM Assumption ($/1K views)", 2.0, 8.0, 4.5, 0.5)
df = build_roi_table(costs, yt_videos, cpm)

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------

kpi_row([
    {"label": "Avg Production Cost", "value": format_currency(df["Production Cost"].mean())},
    {"label": "Avg Revenue/Video", "value": format_currency(df["Est. Revenue"].mean())},
    {"label": "Avg ROI", "value": f"{df['ROI %'].mean():.0f}%"},
    {"label": "Videos Analyzed", "value": str(len(df))},
])

st.markdown("---")

# ---------------------------------------------------------------------------
# Scatter Plot: Cost vs Revenue
# ---------------------------------------------------------------------------

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Production Cost vs. Revenue")
    fig_scatter = px.scatter(
        df, x="Production Cost", y="Est. Revenue", size="Views",
        color="Format", hover_name="Title",
        color_discrete_sequence=CHART_COLORS, size_max=40,
    )
    fig_scatter.add_shape(
        type="line", x0=0, y0=0,
        x1=df["Production Cost"].max() * 1.1,
        y1=df["Production Cost"].max() * 1.1,
        line={"color": "rgba(255,255,255,0.3)", "dash": "dash"},
    )
    fig_scatter.update_layout(
        height=450, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis_tickprefix="$", xaxis_tickformat=",",
        yaxis_tickprefix="$", yaxis_tickformat=",",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        xaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.1)"},
        yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.1)"},
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col2:
    st.subheader("Avg Cost/1K Views by Format")
    fmt_df = df.groupby("Format").agg({
        "Cost/1K Views": "mean", "ROI %": "mean", "Views": "sum",
    }).reset_index().sort_values("Cost/1K Views")
    fig_bar = go.Figure(data=[go.Bar(
        x=fmt_df["Format"], y=fmt_df["Cost/1K Views"],
        marker_color=CHART_COLORS[:len(fmt_df)],
        text=[f"${v:.2f}" for v in fmt_df["Cost/1K Views"]], textposition="auto",
    )])
    fig_bar.update_layout(
        height=450, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis_tickprefix="$", yaxis_title="Cost per 1K Views",
        xaxis={"showgrid": False},
        yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.1)"},
        margin={"l": 50, "r": 20, "t": 10, "b": 40},
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------

st.markdown("---")
col_top, col_bottom = st.columns(2)
num_fmt = {"Production Cost": st.column_config.NumberColumn(format="$%.0f"),
           "Est. Revenue": st.column_config.NumberColumn(format="$%.0f"),
           "Views": st.column_config.NumberColumn(format="%d"),
           "ROI %": st.column_config.NumberColumn(format="%.1f%%")}

with col_top:
    st.subheader("Top 5 by ROI")
    st.dataframe(df.nlargest(5, "ROI %")[["Title", "Format", "Views", "Production Cost", "Est. Revenue", "ROI %"]],
                 use_container_width=True, hide_index=True, column_config=num_fmt)

with col_bottom:
    st.subheader("Bottom 5 by ROI")
    st.dataframe(df.nsmallest(5, "ROI %")[["Title", "Format", "Views", "Production Cost", "Est. Revenue", "ROI %"]],
                 use_container_width=True, hide_index=True, column_config=num_fmt)

# ---------------------------------------------------------------------------
# Full Table
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Full Video ROI Table")
st.dataframe(
    df.sort_values("ROI %", ascending=False), use_container_width=True, hide_index=True,
    column_config={
        "Production Cost": st.column_config.NumberColumn(format="$%.0f"),
        "Est. Revenue": st.column_config.NumberColumn(format="$%.0f"),
        "Views": st.column_config.NumberColumn(format="%d"),
        "ROI %": st.column_config.NumberColumn(format="%.1f%%"),
        "Margin %": st.column_config.NumberColumn(format="%.1f%%"),
        "Cost/View": st.column_config.NumberColumn(format="$%.4f"),
        "Cost/1K Views": st.column_config.NumberColumn(format="$%.2f"),
    },
)
