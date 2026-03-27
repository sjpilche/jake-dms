"""Jake-DMS CFO Command Center — Streamlit entry point.

Run: poetry run streamlit run src/demo/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is on sys.path (required for Streamlit Cloud)
_root = str(Path(__file__).resolve().parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st

from src.demo.mock_data import ensure_demo_data
from src.demo.theme import (
    CARD_BG,
    GREEN,
    GOLD,
    RED,
    TEAL,
    TEAL_LIGHT,
    TEXT_SECONDARY,
    format_currency,
    format_number,
    inject_tabular_nums,
    page_config,
    render_sidebar,
)
from src.demo.youtube_public import YouTubePublicClient

# Must be first Streamlit call
page_config()

# Ensure database exists and is seeded
ensure_demo_data()

# Sidebar
render_sidebar()
inject_tabular_nums()


# ---------------------------------------------------------------------------
# Live data
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def _load_yt_stats() -> tuple[int, int]:
    try:
        yt = YouTubePublicClient()
        ch = yt.get_channel_stats()
        return ch.subscriber_count, ch.view_count
    except Exception as exc:
        from loguru import logger
        logger.warning(f"YouTube channel stats unavailable, using fallback: {exc}")
        return 20_600_000, 19_000_000_000


subs, total_views = _load_yt_stats()

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <div style="text-align: center; padding: 40px 20px 20px;">
        <h1 style="color: {TEAL}; font-size: 44px; margin-bottom: 8px;">
            DMS CFO Command Center
        </h1>
        <p style="color: {TEXT_SECONDARY}; font-size: 18px; max-width: 680px;
           margin: 0 auto 24px;">
            Financial operating system for Dhar Mann Studios.
            Real YouTube data. Sage Intacct integration-ready.
            6 autonomous agents running 24/7.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Headline KPIs — Dhar's actual numbers
# ---------------------------------------------------------------------------

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Annual Revenue", "$78M", "+12% YoY")
with c2:
    st.metric("Operating Margin", "26%", "+2.3pp")
with c3:
    st.metric("YouTube Subs", format_number(subs), "+1.2M YoY")
with c4:
    st.metric("Total Views", format_number(total_views))
with c5:
    st.metric("Platform Concentration", "51%", "Target: <40%", delta_color="inverse")

# ---------------------------------------------------------------------------
# CFO Insight — the "so what"
# ---------------------------------------------------------------------------

st.markdown("---")

st.markdown(
    f"""
    <div style="background-color: {CARD_BG}; border-radius: 8px; padding: 20px 24px;
         border-left: 4px solid {TEAL};">
        <p style="color: {TEAL_LIGHT}; font-weight: bold; font-size: 15px;
           margin-bottom: 8px;">
            CFO Briefing
        </p>
        <p style="color: #FAFAFA; font-size: 14px; line-height: 1.7; margin: 0;">
            DMS is generating <b>$78M/yr</b> at a healthy <b>26% operating margin</b>,
            but <b>51% of revenue flows through YouTube + Facebook</b> — well above the
            40% concentration safety threshold. The immediate CFO priority is diversifying
            revenue streams (licensing, merchandise, brand deals) while maintaining margin
            discipline. Cash position is strong at <b>~$8M</b> with 5+ weeks of runway,
            but biweekly payroll cycles create predictable dips that need active management.
            Content ROI analysis shows long-form episodes deliver <b>3-4x better ROI</b>
            than shorts — a key input for production budget allocation.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("")

# ---------------------------------------------------------------------------
# What this system does
# ---------------------------------------------------------------------------

col_left, col_right = st.columns(2)

with col_left:
    st.markdown(
        f"""
        <div style="background-color: {CARD_BG}; border-radius: 8px; padding: 20px 24px;">
            <p style="color: {TEAL_LIGHT}; font-weight: bold; font-size: 15px;
               margin-bottom: 12px;">
                What This System Replaces
            </p>
            <p style="color: {RED}; font-size: 13px; margin: 4px 0;">
                Manual spreadsheet reconciliation (hours/week)
            </p>
            <p style="color: {RED}; font-size: 13px; margin: 4px 0;">
                Guesswork on which content formats are profitable
            </p>
            <p style="color: {RED}; font-size: 13px; margin: 4px 0;">
                Reactive cash management (checking balances ad hoc)
            </p>
            <p style="color: {RED}; font-size: 13px; margin: 4px 0;">
                Multi-day monthly close cycles
            </p>
            <p style="color: {RED}; font-size: 13px; margin: 4px 0;">
                Board decks assembled manually every month
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_right:
    st.markdown(
        f"""
        <div style="background-color: {CARD_BG}; border-radius: 8px; padding: 20px 24px;">
            <p style="color: {TEAL_LIGHT}; font-weight: bold; font-size: 15px;
               margin-bottom: 12px;">
                What You Get on Day 1
            </p>
            <p style="color: {GREEN}; font-size: 13px; margin: 4px 0;">
                Daily automated platform revenue reconciliation
            </p>
            <p style="color: {GREEN}; font-size: 13px; margin: 4px 0;">
                Episode-level ROI with real YouTube view data
            </p>
            <p style="color: {GREEN}; font-size: 13px; margin: 4px 0;">
                13-week rolling cash forecast, updated every morning
            </p>
            <p style="color: {GREEN}; font-size: 13px; margin: 4px 0;">
                Monthly close in hours, not days
            </p>
            <p style="color: {GREEN}; font-size: 13px; margin: 4px 0;">
                One-click investor packages (PDF + Excel)
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Navigation cards
# ---------------------------------------------------------------------------

st.markdown(
    f'<p style="color: {TEAL_LIGHT}; font-weight: bold; font-size: 15px;">'
    "Explore the Dashboard</p>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    - **Content ROI** — Which episodes make money? Cost-per-view by format and crew
    - **Command Center** — Executive overview with live KPIs, alerts, and agent status
    - **Reconciliation** — YouTube/Meta estimated vs. actual received, variance flags
    - **Cash Flow** — 13-week projection with minimum cash threshold monitoring
    - **Investor Package** — Board-ready P&L, concentration analysis, one-click PDF export
    """
)
