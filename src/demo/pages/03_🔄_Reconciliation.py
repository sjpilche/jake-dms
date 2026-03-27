"""Page 3: Reconciliation — Platform revenue vs Intacct GL matching."""

from __future__ import annotations

import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import io

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.db.engine import get_session
from src.db.models import ARAgingRow, ReconRecordRow
from src.demo.mock_data import ensure_demo_data
from src.demo.theme import (
    CHART_COLORS,
    GREEN,
    RED,
    TEAL,
    empty_state,
    format_currency,
    inject_tabular_nums,
    kpi_row,
    page_config,
    page_header,
    render_sidebar,
)

page_config("Reconciliation | DMS CFO")
ensure_demo_data()
render_sidebar()
inject_tabular_nums()
page_header("Platform Reconciliation", "Revenue Matching: Estimated vs. Received")


# ---------------------------------------------------------------------------
# Cached Data Loading
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def load_recon_data() -> pd.DataFrame:
    session = get_session()
    rows = session.query(ReconRecordRow).order_by(ReconRecordRow.period.desc()).all()
    session.close()
    return pd.DataFrame([
        {
            "Period": r.period, "Platform": r.platform,
            "Estimated": float(r.estimated_revenue),
            "Actual": float(r.actual_received),
            "Variance": float(r.variance),
            "Variance %": float(r.variance_pct), "Status": r.status,
        }
        for r in rows
    ])


@st.cache_data(ttl=300)
def load_ar_data() -> pd.DataFrame:
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


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

recon_df = load_recon_data()
ar_df = load_ar_data()

total_estimated = recon_df["Estimated"].sum()
total_actual = recon_df["Actual"].sum()
total_variance = total_actual - total_estimated
flagged_count = (recon_df["Status"] == "Flagged").sum()

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------

kpi_row([
    {"label": "Total Estimated Revenue", "value": format_currency(total_estimated)},
    {"label": "Total Received", "value": format_currency(total_actual)},
    {
        "label": "Net Variance",
        "value": format_currency(abs(total_variance)),
        "delta": f"{'Over' if total_variance > 0 else 'Under'} by {abs(total_variance/total_estimated*100):.1f}%",
        "delta_color": "normal" if abs(total_variance / total_estimated) < 0.05 else "inverse",
    },
    {"label": "Flagged Items", "value": str(flagged_count), "delta": f"of {len(recon_df)} total"},
])

# ---------------------------------------------------------------------------
# CFO Narrative
# ---------------------------------------------------------------------------

if not recon_df.empty:
    worst_platform = recon_df.groupby("Platform")["Variance %"].apply(
        lambda x: x.abs().mean()
    ).idxmax()
    worst_var = recon_df.groupby("Platform")["Variance %"].apply(
        lambda x: x.abs().mean()
    ).max()
    matched_pct = ((recon_df["Status"] == "Matched").sum() / len(recon_df) * 100)

    st.markdown(
        f"> **Insight:** **{matched_pct:.0f}%** of revenue lines reconcile within 5% tolerance. "
        f"**{worst_platform}** has the highest avg variance at **{worst_var:.1f}%** — "
        f"likely due to payout timing differences. "
        f"**{flagged_count} items** need manual review this period. "
        f"Net variance of {format_currency(abs(total_variance))} is "
        f"{'within acceptable range.' if abs(total_variance / total_estimated) < 0.05 else 'above 5% threshold — investigate immediately.'}"
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Reconciliation by Period")
    if not recon_df.empty:
        period_df = recon_df.groupby("Period").agg(
            {"Estimated": "sum", "Actual": "sum"}
        ).reset_index().sort_values("Period")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=period_df["Period"], y=period_df["Estimated"],
                             name="Estimated", marker_color=TEAL, opacity=0.7))
        fig.add_trace(go.Bar(x=period_df["Period"], y=period_df["Actual"],
                             name="Actual Received", marker_color=CHART_COLORS[1], opacity=0.7))
        fig.update_layout(
            barmode="group", height=400,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis_tickprefix="$", yaxis_tickformat=",",
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
            margin={"l": 50, "r": 20, "t": 30, "b": 40},
            xaxis={"showgrid": False},
            yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.1)"},
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        empty_state("No reconciliation data available for charting.")

with col2:
    st.subheader("Variance by Platform")
    if not recon_df.empty:
        plat_var = recon_df.groupby("Platform").agg(
            {"Variance %": "mean", "Variance": "sum"}
        ).reset_index()
        colors = [GREEN if v < 5 else RED for v in plat_var["Variance %"].abs()]
        bar_text = [
            f"{'▲' if v > 0 else '▼'} {v:+.1f}%" for v in plat_var["Variance %"]
        ]
        fig_var = go.Figure(data=[go.Bar(
            x=plat_var["Platform"], y=plat_var["Variance %"],
            marker_color=colors,
            text=bar_text, textposition="auto",
        )])
        fig_var.add_hline(y=5, line_dash="dash", line_color=RED, opacity=0.5,
                          annotation_text="5% threshold")
        fig_var.add_hline(y=-5, line_dash="dash", line_color=RED, opacity=0.5)
        fig_var.update_layout(
            height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title="Avg Variance %",
            margin={"l": 50, "r": 20, "t": 30, "b": 40},
            xaxis={"showgrid": False},
            yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.1)"},
        )
        st.plotly_chart(fig_var, use_container_width=True)
    else:
        empty_state("No variance data available.")

# ---------------------------------------------------------------------------
# Reconciliation Detail Table
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Reconciliation Detail")
if not recon_df.empty:
    st.dataframe(
        recon_df.sort_values(["Period", "Platform"], ascending=[False, True]),
        use_container_width=True, hide_index=True,
        column_config={
            "Estimated": st.column_config.NumberColumn(format="$%,.0f"),
            "Actual": st.column_config.NumberColumn(format="$%,.0f"),
            "Variance": st.column_config.NumberColumn(format="$%,.0f"),
            "Variance %": st.column_config.NumberColumn(format="%+.2f%%"),
        },
    )
else:
    empty_state("No reconciliation records found.")

# ---------------------------------------------------------------------------
# AR Aging Detail
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Accounts Receivable Aging")
st.dataframe(
    ar_df, use_container_width=True, hide_index=True,
    column_config={
        "Current": st.column_config.NumberColumn(format="$%,.0f"),
        "1-30 Days": st.column_config.NumberColumn(format="$%,.0f"),
        "31-60 Days": st.column_config.NumberColumn(format="$%,.0f"),
        "90+ Days": st.column_config.NumberColumn(format="$%,.0f"),
        "Total": st.column_config.NumberColumn(format="$%,.0f"),
    },
)

total_over_60 = ar_df["31-60 Days"].sum() + ar_df["90+ Days"].sum()
pct_over_60 = (total_over_60 / ar_df["Total"].sum() * 100) if ar_df["Total"].sum() > 0 else 0
st.info(
    f"**AR Summary:** ${ar_df['Total'].sum():,.0f} total receivables | "
    f"${total_over_60:,.0f} over 60 days ({pct_over_60:.1f}% of total)"
)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

st.markdown("---")
csv_buf = io.StringIO()
recon_df.to_csv(csv_buf, index=False)
st.download_button("Download Reconciliation as CSV", csv_buf.getvalue(), "dms_reconciliation.csv", "text/csv")
