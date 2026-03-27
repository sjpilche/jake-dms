"""Page 6: YouTube Deep Dive — Real channel analysis from Dhar Mann Studios."""

from __future__ import annotations

import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.demo.mock_data import ensure_demo_data
from src.demo.theme import (
    CARD_BG,
    CHART_COLORS,
    GREEN,
    RED,
    TEAL,
    TEAL_LIGHT,
    format_currency,
    format_number,
    inject_tabular_nums,
    kpi_row,
    page_config,
    page_header,
    render_sidebar,
)
from src.demo.youtube_public import YouTubePublicClient

page_config("YouTube Deep Dive | DMS CFO")
ensure_demo_data()
render_sidebar()
inject_tabular_nums()
page_header("YouTube Deep Dive", "Real Data from Dhar Mann Studios Channel")


# ---------------------------------------------------------------------------
# Load real YouTube data
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def load_channel_data() -> dict | None:
    try:
        yt = YouTubePublicClient()
        ch = yt.get_channel_stats()
        return {
            "subscribers": ch.subscriber_count,
            "views": ch.view_count,
            "videos": ch.video_count,
        }
    except Exception as exc:
        from loguru import logger
        logger.warning(f"YouTube channel stats unavailable: {exc}")
        return None


@st.cache_data(ttl=3600)
def load_recent_videos() -> list[dict]:
    try:
        yt = YouTubePublicClient()
        videos = yt.get_recent_videos(max_results=50)
        return [
            {
                "title": v.title,
                "video_id": v.video_id,
                "view_count": v.view_count,
                "published": v.published_at[:10] if v.published_at else "Unknown",
                "duration_sec": v.duration_seconds,
            }
            for v in videos
        ]
    except Exception as exc:
        from loguru import logger
        logger.warning(f"Failed to load recent YouTube videos: {exc}")
        return []


channel = load_channel_data()
videos = load_recent_videos()

# ---------------------------------------------------------------------------
# Channel KPIs
# ---------------------------------------------------------------------------

if channel:
    avg_views_per_video = channel["views"] // channel["videos"] if channel["videos"] > 0 else 0
    kpi_row([
        {"label": "Subscribers", "value": format_number(channel["subscribers"]), "delta": "Top 0.01% globally"},
        {"label": "Lifetime Views", "value": format_number(channel["views"])},
        {"label": "Total Videos", "value": f"{channel['videos']:,}"},
        {"label": "Avg Views/Video", "value": format_number(avg_views_per_video)},
    ])
else:
    st.warning("YouTube API unavailable — add YOUTUBE_API_KEY to .env for live data")

# ---------------------------------------------------------------------------
# CFO Narrative
# ---------------------------------------------------------------------------

if videos:
    df = pd.DataFrame(videos)
    total_recent_views = df["view_count"].sum()
    avg_recent_views = df["view_count"].mean()
    top_video = df.loc[df["view_count"].idxmax()]
    median_views = df["view_count"].median()

    # Classify by duration
    df["format"] = df["duration_sec"].apply(
        lambda s: "Short (<60s)" if s < 60
        else "Mid (1-10m)" if s < 600
        else "Long (10m+)"
    )

    cpm = st.sidebar.slider("CPM Assumption ($/1K views)", 2.0, 8.0, 4.5, 0.5)
    df["est_revenue"] = (df["view_count"] * cpm / 1000).round(2)

    st.markdown(
        f"> **Insight:** Across the last **{len(df)} videos**, DMS generated "
        f"**{format_number(total_recent_views)} total views** — averaging "
        f"**{format_number(int(avg_recent_views))} per video**. "
        f"The top performer hit **{format_number(top_video['view_count'])} views**. "
        f"Median views ({format_number(int(median_views))}) are "
        f"{'above' if median_views > 5_000_000 else 'near'} the 5M benchmark "
        f"for top-tier creator channels. At ${cpm:.2f} CPM, this catalog generated an "
        f"estimated **{format_currency(df['est_revenue'].sum())}** in ad revenue."
    )

    st.markdown("---")

    # ---------------------------------------------------------------------------
    # Views Distribution
    # ---------------------------------------------------------------------------

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Views by Video (Recent 50)")
        fig_bar = go.Figure(data=[go.Bar(
            x=list(range(1, len(df) + 1)),
            y=df.sort_values("view_count", ascending=False)["view_count"].values,
            marker_color=TEAL,
            hovertext=df.sort_values("view_count", ascending=False)["title"].values,
        )])
        # Industry benchmark line
        fig_bar.add_hline(
            y=5_000_000, line_dash="dash", line_color=TEAL_LIGHT, opacity=0.5,
            annotation_text="5M benchmark",
            annotation_position="top right",
        )
        fig_bar.update_layout(
            height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Video Rank", yaxis_title="Views",
            yaxis_tickformat=",",
            margin={"l": 60, "r": 20, "t": 10, "b": 40},
            xaxis={"showgrid": False},
            yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.1)"},
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.subheader("Performance by Format")
        fmt_summary = df.groupby("format").agg(
            videos=("view_count", "count"),
            avg_views=("view_count", "mean"),
            total_revenue=("est_revenue", "sum"),
        ).reset_index().sort_values("avg_views", ascending=False)

        fig_fmt = go.Figure(data=[go.Bar(
            x=fmt_summary["format"],
            y=fmt_summary["avg_views"],
            marker_color=CHART_COLORS[:len(fmt_summary)],
            text=[format_number(int(v)) for v in fmt_summary["avg_views"]],
            textposition="auto",
        )])
        fig_fmt.update_layout(
            height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title="Avg Views per Video", yaxis_tickformat=",",
            margin={"l": 60, "r": 20, "t": 10, "b": 40},
            xaxis={"showgrid": False},
            yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.1)"},
        )
        st.plotly_chart(fig_fmt, use_container_width=True)

    # ---------------------------------------------------------------------------
    # Revenue Estimation Table
    # ---------------------------------------------------------------------------

    st.markdown("---")
    st.subheader("Estimated Revenue by Format")

    fmt_rev = df.groupby("format").agg(
        count=("view_count", "count"),
        total_views=("view_count", "sum"),
        avg_views=("view_count", "mean"),
        est_revenue=("est_revenue", "sum"),
    ).reset_index().sort_values("est_revenue", ascending=False)
    fmt_rev["rev_per_video"] = fmt_rev["est_revenue"] / fmt_rev["count"]

    st.dataframe(
        fmt_rev.rename(columns={
            "format": "Format", "count": "Videos", "total_views": "Total Views",
            "avg_views": "Avg Views", "est_revenue": "Est. Revenue",
            "rev_per_video": "Revenue/Video",
        }),
        use_container_width=True, hide_index=True,
        column_config={
            "Total Views": st.column_config.NumberColumn(format="%d"),
            "Avg Views": st.column_config.NumberColumn(format="%,.0f"),
            "Est. Revenue": st.column_config.NumberColumn(format="$%,.0f"),
            "Revenue/Video": st.column_config.NumberColumn(format="$%,.0f"),
        },
    )

    # ---------------------------------------------------------------------------
    # Top 10 Videos
    # ---------------------------------------------------------------------------

    st.markdown("---")
    st.subheader("Top 10 Videos by Views")

    top10 = df.nlargest(10, "view_count")[["title", "view_count", "est_revenue", "format", "published"]]
    top10 = top10.rename(columns={
        "title": "Title", "view_count": "Views",
        "est_revenue": "Est. Revenue", "format": "Format", "published": "Published",
    })
    st.dataframe(
        top10, use_container_width=True, hide_index=True,
        column_config={
            "Views": st.column_config.NumberColumn(format="%,d"),
            "Est. Revenue": st.column_config.NumberColumn(format="$%,.0f"),
        },
    )

    # ---------------------------------------------------------------------------
    # Publishing Cadence
    # ---------------------------------------------------------------------------

    st.markdown("---")
    st.subheader("Publishing Cadence")

    df["pub_date"] = pd.to_datetime(df["published"], errors="coerce")
    pub_df = df.dropna(subset=["pub_date"]).sort_values("pub_date")
    if len(pub_df) >= 2:
        pub_df["days_between"] = pub_df["pub_date"].diff().dt.days
        avg_cadence = pub_df["days_between"].mean()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Avg Days Between Uploads", f"{avg_cadence:.1f}")
        with c2:
            st.metric("Videos/Month (est.)", f"{30 / avg_cadence:.1f}" if avg_cadence > 0 else "N/A")
        with c3:
            st.metric("Content Library Size", f"{channel['videos']:,}" if channel else "N/A")

        st.markdown(
            f"> **Insight:** DMS publishes roughly every **{avg_cadence:.0f} days** — "
            f"that's about **{30 / avg_cadence:.0f} videos/month**. "
            f"Consistent cadence is critical for YouTube algorithm performance. "
            f"{'This pace is strong for a studio this size.' if avg_cadence < 5 else 'There may be room to increase frequency for algorithmic boost.'}"
        )

else:
    st.info("Add YOUTUBE_API_KEY to .env to see real channel analysis.")
