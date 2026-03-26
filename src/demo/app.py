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
from src.demo.theme import TEAL, TEXT_SECONDARY, page_config, render_sidebar

# Must be first Streamlit call
page_config()

# Ensure database exists and is seeded
ensure_demo_data()

# Sidebar
render_sidebar()

# Main content
st.markdown(
    f"""
    <div style="text-align: center; padding: 60px 20px;">
        <h1 style="color: {TEAL}; font-size: 48px;">DMS CFO Command Center</h1>
        <p style="color: {TEXT_SECONDARY}; font-size: 20px; max-width: 600px; margin: 20px auto;">
            AI-powered financial intelligence for Dhar Mann Studios.
            Real YouTube data. Sage Intacct integration-ready.
        </p>
        <div style="background-color: #E63946; color: white; padding: 8px 24px;
             border-radius: 6px; font-weight: bold; display: inline-block;
             font-size: 16px; margin-top: 20px;">
            PROTOTYPE DEMO
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# Quick stats overview
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"### 6")
    st.caption("Agent Domains")
with col2:
    st.markdown(f"### 18")
    st.caption("Specialist Agents")
with col3:
    st.markdown(f"### 5")
    st.caption("Dashboard Views")
with col4:
    st.markdown(f"### Real-Time")
    st.caption("YouTube Data")

st.markdown("---")

st.markdown(
    """
    **Navigate using the sidebar** to explore:
    - **Command Center** — Executive financial overview
    - **Content ROI** — Episode-level profitability analysis
    - **Reconciliation** — Platform revenue vs. Intacct GL matching
    - **Cash Flow** — 13-week rolling forecast
    - **Investor Package** — Board-ready metrics summary
    """
)
