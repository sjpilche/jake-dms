"""Shared Streamlit theme constants and reusable UI components."""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Color Palette
# ---------------------------------------------------------------------------

TEAL = "#0F7173"
TEAL_LIGHT = "#14A3A8"
DARK_BG = "#0E1117"
CARD_BG = "#1E1E2E"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#A0A0A0"
RED = "#E63946"
GREEN = "#2A9D8F"
GOLD = "#E9C46A"
BLUE = "#457B9D"
ORANGE = "#F4A261"
PURPLE = "#7B68EE"

# Chart color sequence
CHART_COLORS = [TEAL, GOLD, RED, BLUE, ORANGE, PURPLE, GREEN, TEAL_LIGHT]

# Business line colors (consistent across all charts)
BIZ_LINE_COLORS = {
    "Core Content": TEAL,
    "5th Quarter": BLUE,
    "Brand Deals": GOLD,
    "Licensing/OTT": ORANGE,
    "Merchandise": PURPLE,
    "Other": TEXT_SECONDARY,
}

PLATFORM_COLORS = {
    "YouTube": "#FF0000",
    "Facebook": "#1877F2",
    "Brand Deals": GOLD,
    "Licensing": ORANGE,
    "Merchandise": PURPLE,
    "Other": TEXT_SECONDARY,
    "TikTok": "#69C9D0",
}


# ---------------------------------------------------------------------------
# UI Components
# ---------------------------------------------------------------------------

def page_config(title: str = "DMS CFO Command Center") -> None:
    """Set page config — must be called first in every page."""
    st.set_page_config(
        page_title=title,
        page_icon="$",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def page_header(title: str, subtitle: str = "") -> None:
    """Render page header with DEMO badge."""
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"## {title}")
        if subtitle:
            st.caption(subtitle)
    with col2:
        st.markdown(
            '<div style="background-color: #E63946; color: white; padding: 4px 12px; '
            'border-radius: 4px; font-weight: bold; text-align: center; '
            'font-size: 14px; margin-top: 12px; cursor: default; '
            'user-select: none; pointer-events: none;">DEMO</div>',
            unsafe_allow_html=True,
        )


def render_sidebar() -> None:
    """Render the shared sidebar with branding and agent pulse."""
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 20px 0;">
                <h2 style="color: {TEAL}; margin-bottom: 0;">DMS CFO</h2>
                <h3 style="color: {TEXT_SECONDARY}; margin-top: 0; border-left: none;">
                    Command Center</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown(
            f'<p style="color: {TEXT_SECONDARY}; font-size: 14px; text-align: center;">'
            "Dhar Mann Studios | Prototype Dashboard</p>",
            unsafe_allow_html=True,
        )
    agent_pulse()


def metric_card(
    label: str,
    value: str,
    delta: str | None = None,
    delta_color: str = "normal",
) -> None:
    """Render a styled metric card."""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def kpi_row(metrics: list[dict]) -> None:
    """Render a row of KPI metric cards.

    Each dict: {"label": str, "value": str, "delta": str|None, "delta_color": str}
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            metric_card(
                label=m["label"],
                value=m["value"],
                delta=m.get("delta"),
                delta_color=m.get("delta_color", "normal"),
            )


def format_currency(amount: float | int, decimals: int = 0) -> str:
    """Format a number as USD currency string."""
    if abs(amount) >= 1_000_000:
        return f"${amount / 1_000_000:,.{decimals}f}M"
    elif abs(amount) >= 1_000:
        return f"${amount / 1_000:,.{decimals}f}K"
    return f"${amount:,.{decimals}f}"


def format_number(n: int) -> str:
    """Format a large number with K/M suffix."""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def status_badge(text: str, color: str) -> str:
    """Return HTML for a colored status badge."""
    return (
        f'<span style="background-color: {color}; color: white; '
        f'padding: 2px 8px; border-radius: 4px; font-size: 12px;">'
        f"{text}</span>"
    )


def inject_tabular_nums() -> None:
    """Inject premium CSS: tabular figures, card styling, smooth transitions."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Premium font */
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        /* Tabular figures for financial data */
        [data-testid="stMetricValue"],
        [data-testid="stDataFrame"] td {{
            font-variant-numeric: tabular-nums;
        }}

        /* Metric card styling */
        [data-testid="stMetric"] {{
            background-color: {CARD_BG};
            border-radius: 8px;
            padding: 12px 16px;
            border: 1px solid rgba(255,255,255,0.06);
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        [data-testid="stMetric"]:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(15,113,115,0.2);
        }}

        /* Metric value emphasis */
        [data-testid="stMetricValue"] {{
            font-weight: 700;
            font-size: 1.6rem !important;
        }}

        /* Subheader accent */
        h3 {{
            border-left: 3px solid {TEAL};
            padding-left: 12px;
        }}

        /* Blockquote insight styling */
        blockquote {{
            background-color: {CARD_BG};
            border-left: 4px solid {TEAL};
            border-radius: 0 8px 8px 0;
            padding: 12px 16px;
            margin: 8px 0 16px;
        }}
        blockquote p {{
            color: #d0d0d0 !important;
            font-size: 14px;
            line-height: 1.6;
        }}

        /* Smooth dataframe styling */
        [data-testid="stDataFrame"] {{
            border-radius: 8px;
            overflow: hidden;
        }}

        /* Download button styling */
        [data-testid="stDownloadButton"] button {{
            border: 1px solid {TEAL} !important;
            color: {TEAL} !important;
            transition: all 0.15s ease;
        }}
        [data-testid="stDownloadButton"] button:hover {{
            background-color: {TEAL} !important;
            color: white !important;
        }}

        /* Sidebar polish */
        [data-testid="stSidebar"] {{
            border-right: 1px solid rgba(255,255,255,0.06);
        }}

        /* Divider subtlety */
        hr {{
            border-color: rgba(255,255,255,0.06) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def card_container(content_fn: object) -> None:
    """Wrap a callable's output in a styled card container."""
    st.markdown(
        f'<div style="background-color: {CARD_BG}; border-radius: 8px; '
        f'padding: 16px; margin-bottom: 12px;">',
        unsafe_allow_html=True,
    )
    content_fn()  # type: ignore[operator]
    st.markdown("</div>", unsafe_allow_html=True)


def empty_state(message: str = "No data available.") -> None:
    """Show a helpful empty state message when no data is present."""
    st.info(message)


def agent_pulse() -> None:
    """Render a live agent pulse status bar in the sidebar."""
    from datetime import datetime

    now = datetime.now()
    next_recon = now.replace(hour=7, minute=0, second=0)
    if now.hour >= 7:
        from datetime import timedelta
        next_recon += timedelta(days=1)
    hours_until = (next_recon - now).total_seconds() / 3600

    with st.sidebar:
        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; border-radius: 8px; padding: 12px;
                 margin-top: 12px; border: 1px solid rgba(255,255,255,0.06);">
                <p style="color: {TEAL_LIGHT}; font-weight: 600; font-size: 13px;
                   margin: 0 0 8px;">Agent Status</p>

                <div style="display: flex; align-items: center; margin: 4px 0;">
                    <span style="width: 8px; height: 8px; border-radius: 50%;
                          background-color: {GREEN}; display: inline-block;
                          margin-right: 8px; box-shadow: 0 0 6px {GREEN};
                          animation: pulse 2s infinite;"></span>
                    <span style="color: #ccc; font-size: 12px;">
                        Platform Recon — daily 7:00 AM PT
                    </span>
                </div>
                <div style="display: flex; align-items: center; margin: 4px 0;">
                    <span style="width: 8px; height: 8px; border-radius: 50%;
                          background-color: {GREEN}; display: inline-block;
                          margin-right: 8px; box-shadow: 0 0 6px {GREEN};
                          animation: pulse 2s infinite 0.3s;"></span>
                    <span style="color: #ccc; font-size: 12px;">
                        Cash Forecast — daily 7:15 AM PT
                    </span>
                </div>
                <div style="display: flex; align-items: center; margin: 4px 0;">
                    <span style="width: 8px; height: 8px; border-radius: 50%;
                          background-color: {GREEN}; display: inline-block;
                          margin-right: 8px; box-shadow: 0 0 6px {GREEN};
                          animation: pulse 2s infinite 0.6s;"></span>
                    <span style="color: #ccc; font-size: 12px;">
                        Content ROI — weekly Mon 8:00 AM
                    </span>
                </div>
                <div style="display: flex; align-items: center; margin: 4px 0;">
                    <span style="width: 8px; height: 8px; border-radius: 50%;
                          background-color: {GREEN}; display: inline-block;
                          margin-right: 8px; box-shadow: 0 0 6px {GREEN};
                          animation: pulse 2s infinite 0.9s;"></span>
                    <span style="color: #ccc; font-size: 12px;">
                        Concentration — monthly 5th
                    </span>
                </div>
                <div style="display: flex; align-items: center; margin: 4px 0;">
                    <span style="width: 8px; height: 8px; border-radius: 50%;
                          background-color: {GOLD}; display: inline-block;
                          margin-right: 8px;"></span>
                    <span style="color: #ccc; font-size: 12px;">
                        Investor Report — on demand
                    </span>
                </div>

                <p style="color: #666; font-size: 11px; margin: 8px 0 0;">
                    Next run: Recon in {hours_until:.1f}h
                </p>
            </div>

            <style>
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.4; }}
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
