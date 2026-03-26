"""Page 4: Cash Flow — 13-week rolling forecast."""

from __future__ import annotations

import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import random
from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.db.engine import get_session
from src.db.models import CashBalanceRow
from src.demo.mock_data import TODAY, ensure_demo_data
from src.demo.theme import (
    CHART_COLORS,
    RED,
    TEAL,
    format_currency,
    kpi_row,
    page_config,
    page_header,
    render_sidebar,
)

page_config("Cash Flow | DMS CFO")
ensure_demo_data()
render_sidebar()
page_header("Cash Flow Forecast", "13-Week Rolling Projection")


# ---------------------------------------------------------------------------
# Cached Data
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def load_current_cash() -> float:
    session = get_session()
    rows = session.query(CashBalanceRow).all()
    session.close()
    return sum(float(r.balance) for r in rows)


@st.cache_data(ttl=300)
def generate_forecast(current_cash: float) -> pd.DataFrame:
    rng = random.Random(42)

    weekly_inflows = {
        "Platform Payouts": 920_000, "Brand Deal Payments": 350_000,
        "Licensing Revenue": 180_000, "Other Income": 50_000,
    }
    weekly_outflows = {
        "Payroll (biweekly)": 538_000, "Production Costs": 280_000,
        "Talent Payments": 165_000, "Facilities": 77_000,
        "Technology": 58_000, "Marketing": 115_000, "G&A": 96_000,
    }
    min_cash_threshold = sum(weekly_outflows.values()) * 2

    weeks = []
    running_cash = current_cash

    for w in range(1, 14):
        week_start = TODAY + timedelta(weeks=w - 1)

        inflows = {}
        for source, base in weekly_inflows.items():
            if source == "Platform Payouts" and week_start.day < 21:
                mult = rng.uniform(0.4, 0.7)
            else:
                mult = rng.uniform(0.85, 1.15)
            inflows[source] = round(base * mult, 2)

        outflows = {}
        for category, base in weekly_outflows.items():
            if category == "Payroll (biweekly)" and w % 2 != 0:
                outflows[category] = round(base * 2, 2)
            else:
                outflows[category] = 0 if "Payroll" in category else round(base * rng.uniform(0.9, 1.1), 2)

        total_in = sum(inflows.values())
        total_out = sum(outflows.values())
        net = total_in - total_out
        closing = running_cash + net

        weeks.append({
            "Week": w, "Week Start": week_start.strftime("%m/%d"),
            "Opening Cash": running_cash,
            "Platform Payouts": inflows["Platform Payouts"],
            "Brand Deal Payments": inflows["Brand Deal Payments"],
            "Licensing Revenue": inflows["Licensing Revenue"],
            "Other Income": inflows["Other Income"],
            "Total Inflows": total_in,
            "Payroll": outflows["Payroll (biweekly)"],
            "Production": outflows.get("Production Costs", 0),
            "Talent": outflows.get("Talent Payments", 0),
            "Facilities": outflows.get("Facilities", 0),
            "Technology": outflows.get("Technology", 0),
            "Marketing": outflows.get("Marketing", 0),
            "G&A": outflows.get("G&A", 0),
            "Total Outflows": total_out,
            "Net Change": net, "Closing Cash": closing,
            "Below Minimum": closing < min_cash_threshold,
        })
        running_cash = closing

    return pd.DataFrame(weeks)


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

current_cash = load_current_cash()
df = generate_forecast(current_cash)
min_cash_threshold = df["Total Outflows"].mean() * 2
projected_low = df["Closing Cash"].min()
avg_burn = df["Total Outflows"].mean()
weeks_runway = current_cash / avg_burn if avg_burn > 0 else 999

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------

kpi_row([
    {"label": "Current Cash", "value": format_currency(current_cash)},
    {
        "label": "Projected 13-Wk Low",
        "value": format_currency(projected_low),
        "delta": "Above minimum" if projected_low > min_cash_threshold else "BELOW MINIMUM",
        "delta_color": "normal" if projected_low > min_cash_threshold else "inverse",
    },
    {"label": "Avg Weekly Outflow", "value": format_currency(avg_burn)},
    {"label": "Weeks of Runway", "value": f"{weeks_runway:.1f}"},
])

st.markdown("---")

# ---------------------------------------------------------------------------
# Forecast Chart
# ---------------------------------------------------------------------------

st.subheader("13-Week Cash Projection")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df["Week Start"], y=df["Closing Cash"], mode="lines+markers",
    name="Projected Cash", line={"color": TEAL, "width": 3}, marker={"size": 8},
    fill="tozeroy", fillcolor="rgba(15, 113, 115, 0.1)",
))
fig.add_hline(y=min_cash_threshold, line_dash="dash", line_color=RED,
              annotation_text=f"Minimum Cash ({format_currency(min_cash_threshold)})",
              annotation_position="top right")
fig.update_layout(
    height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    yaxis_tickprefix="$", yaxis_tickformat=",",
    xaxis_title="Week Starting", yaxis_title="Cash Balance",
    margin={"l": 60, "r": 30, "t": 30, "b": 50},
    xaxis={"showgrid": False},
    yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.1)"},
)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Inflows vs Outflows
# ---------------------------------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    st.subheader("Weekly Inflows by Source")
    fig_in = go.Figure()
    for i, source in enumerate(["Platform Payouts", "Brand Deal Payments", "Licensing Revenue", "Other Income"]):
        fig_in.add_trace(go.Bar(x=df["Week Start"], y=df[source], name=source, marker_color=CHART_COLORS[i]))
    fig_in.update_layout(
        barmode="stack", height=350,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis_tickprefix="$", yaxis_tickformat=",",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "font": {"size": 10}},
        margin={"l": 50, "r": 10, "t": 30, "b": 40},
        xaxis={"showgrid": False}, yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.1)"},
    )
    st.plotly_chart(fig_in, use_container_width=True)

with col2:
    st.subheader("Weekly Outflows by Category")
    fig_out = go.Figure()
    for i, cat in enumerate(["Payroll", "Production", "Talent", "Facilities", "Technology", "Marketing", "G&A"]):
        fig_out.add_trace(go.Bar(x=df["Week Start"], y=df[cat], name=cat, marker_color=CHART_COLORS[i % len(CHART_COLORS)]))
    fig_out.update_layout(
        barmode="stack", height=350,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis_tickprefix="$", yaxis_tickformat=",",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "font": {"size": 10}},
        margin={"l": 50, "r": 10, "t": 30, "b": 40},
        xaxis={"showgrid": False}, yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.1)"},
    )
    st.plotly_chart(fig_out, use_container_width=True)

# ---------------------------------------------------------------------------
# Detail Table
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Week-by-Week Detail")
st.dataframe(
    df[["Week", "Week Start", "Opening Cash", "Total Inflows", "Total Outflows", "Net Change", "Closing Cash"]],
    use_container_width=True, hide_index=True,
    column_config={
        "Opening Cash": st.column_config.NumberColumn(format="$%,.0f"),
        "Total Inflows": st.column_config.NumberColumn(format="$%,.0f"),
        "Total Outflows": st.column_config.NumberColumn(format="$%,.0f"),
        "Net Change": st.column_config.NumberColumn(format="$%+,.0f"),
        "Closing Cash": st.column_config.NumberColumn(format="$%,.0f"),
    },
)
