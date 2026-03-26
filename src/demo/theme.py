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
    "TikTok": "#000000",
}


# ---------------------------------------------------------------------------
# UI Components
# ---------------------------------------------------------------------------

def page_config(title: str = "DMS CFO Command Center") -> None:
    """Set page config — must be called first in every page."""
    st.set_page_config(
        page_title=title,
        page_icon="📊",
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
            'font-size: 14px; margin-top: 12px;">DEMO</div>',
            unsafe_allow_html=True,
        )


def render_sidebar() -> None:
    """Render the shared sidebar with branding."""
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 20px 0;">
                <h2 style="color: {TEAL}; margin-bottom: 0;">DMS CFO</h2>
                <h3 style="color: {TEXT_SECONDARY}; margin-top: 0;">Command Center</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown(
            f'<p style="color: {TEXT_SECONDARY}; font-size: 12px; text-align: center;">'
            "Dhar Mann Studios | Prototype Dashboard</p>",
            unsafe_allow_html=True,
        )


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
