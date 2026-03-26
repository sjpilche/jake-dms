"""Build 3: Executive Summary PDF — 2-page interview leave-behind.

Generates a professional, teal-accented PDF document summarizing:
1. What I bring (financial operating system, not just a CFO)
2. The 6 agent domains
3. Day 1-100 milestones
4. The demo dashboard
5. Background

Run: python -m src.executive_summary
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from loguru import logger

from src.core.config import get_settings

# ---------------------------------------------------------------------------
# Design Constants
# ---------------------------------------------------------------------------

TEAL = colors.HexColor("#0F7173")
TEAL_LIGHT = colors.HexColor("#14A3A8")
DARK = colors.HexColor("#1A1A2E")
GRAY = colors.HexColor("#6C757D")
LIGHT_BG = colors.HexColor("#F8F9FA")
WHITE = colors.white


def _styles() -> dict[str, ParagraphStyle]:
    """Build custom paragraph styles."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title", parent=base["Title"],
            fontSize=28, textColor=TEAL, spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=base["Normal"],
            fontSize=13, textColor=GRAY, spaceAfter=16,
            fontName="Helvetica",
        ),
        "section": ParagraphStyle(
            "Section", parent=base["Heading2"],
            fontSize=14, textColor=TEAL, spaceBefore=14, spaceAfter=6,
            fontName="Helvetica-Bold",
            borderWidth=0, borderPadding=0,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["Normal"],
            fontSize=10, leading=14, textColor=DARK,
            fontName="Helvetica", alignment=TA_JUSTIFY,
        ),
        "body_bold": ParagraphStyle(
            "BodyBold", parent=base["Normal"],
            fontSize=10, leading=14, textColor=DARK,
            fontName="Helvetica-Bold",
        ),
        "small": ParagraphStyle(
            "Small", parent=base["Normal"],
            fontSize=8.5, leading=11, textColor=GRAY,
            fontName="Helvetica",
        ),
        "center": ParagraphStyle(
            "Center", parent=base["Normal"],
            fontSize=10, textColor=DARK, alignment=TA_CENTER,
            fontName="Helvetica",
        ),
        "footer": ParagraphStyle(
            "Footer", parent=base["Normal"],
            fontSize=8, textColor=GRAY, alignment=TA_CENTER,
            fontName="Helvetica-Oblique",
        ),
    }


def generate_executive_summary(output_path: Path | None = None) -> Path:
    """Generate the 2-page executive summary PDF."""
    settings = get_settings()
    if output_path is None:
        output_dir = settings.DATA_DIR / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "executive_summary.pdf"

    s = _styles()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        topMargin=0.6 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    elements: list = []

    # ===================================================================
    # PAGE 1
    # ===================================================================

    # Header
    elements.append(Paragraph("Jake Pilcher", s["title"]))
    elements.append(Paragraph(
        "CFO &amp; Financial Systems Architect  |  Dhar Mann Studios",
        s["subtitle"],
    ))
    elements.append(HRFlowable(
        width="100%", thickness=2, color=TEAL,
        spaceAfter=12, spaceBefore=0,
    ))

    # --- Section 1: What I Bring ---
    elements.append(Paragraph("What I Bring", s["section"]))
    elements.append(Paragraph(
        "I don't just fill the CFO seat — I install a <b>financial operating system</b>. "
        "Within my first 100 days, DMS will have an AI-powered CFO command center that "
        "automates reconciliation, forecasts cash flow, tracks content ROI at the episode "
        "level, and monitors revenue concentration in real time. This isn't a pitch — "
        "the prototype is already built, running against your actual YouTube data.",
        s["body"],
    ))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "My background: multi-entity CFO with deep experience in construction finance, "
        "job costing, and complex accounting. I've built and deployed a 95-agent autonomous "
        "AI platform from scratch. I understand both the financial rigor DMS needs for its "
        "capital markets strategy and the technology to automate the back office at scale.",
        s["body"],
    ))

    # --- Section 2: The 6 Agent Domains ---
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("The Agent Architecture", s["section"]))
    elements.append(Paragraph(
        "Six autonomous domains covering the full CFO function, integrated with "
        "Sage Intacct and your platform APIs:",
        s["body"],
    ))
    elements.append(Spacer(1, 6))

    agent_data = [
        ["Domain", "What It Does"],
        ["Platform Revenue\nIntelligence",
         "Reconciles YouTube/Meta payouts against Intacct GL daily. "
         "Flags discrepancies > 5%. Eliminates the #1 blind spot in creator finance."],
        ["Content ROI\nEngine",
         "Ties Intacct production costs to YouTube performance data. Answers: "
         "which shows make money? Cost per view by format, crew, and series."],
        ["Cash &amp; Treasury",
         "13-week rolling cash forecast incorporating platform payout schedules, "
         "brand deal terms, payroll, and production spend. Daily AM position alerts."],
        ["Deal &amp; Revenue\nRecognition",
         "Tracks brand deal pipeline, automates ASC 606 rev rec schedules, "
         "monitors deferred revenue balances and collection forecasts."],
        ["Content ROI &amp;\nLibrary Valuation",
         "Revenue attribution by episode, content library residual value "
         "projections, format-level margin analysis for strategic decisions."],
        ["Investor &amp; Board\nReporting",
         "Auto-generates monthly investor packages in < 5 minutes. "
         "Revenue by business line, P&L, KPIs, cash, concentration metrics."],
    ]

    col_widths = [1.4 * inch, 5.1 * inch]
    t = Table(agent_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        # Body
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("LEADING", (0, 1), (-1, -1), 11),
        ("TEXTCOLOR", (0, 1), (-1, -1), DARK),
        # Alternating rows
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)

    # ===================================================================
    # PAGE 2
    # ===================================================================

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Day 1–100 Milestones", s["section"]))

    milestone_data = [
        ["Phase", "Timeline", "Deliverables"],
        ["Month 1:\nFoundation",
         "Days 1–30",
         "• Complete Sage Intacct migration from QuickBooks\n"
         "• Deploy platform reconciliation agent (live, daily)\n"
         "• Establish chart of accounts with business line dimensions\n"
         "• First automated daily cash position report via Telegram"],
        ["Month 2:\nIntelligence",
         "Days 31–60",
         "• Content ROI engine live — episode-level profitability visible\n"
         "• 13-week cash flow forecast operational\n"
         "• Revenue concentration monitor tracking against 40% target\n"
         "• Brand deal rev rec schedules automated (ASC 606)"],
        ["Month 3:\nScale",
         "Days 61–100",
         "• First automated investor package generated (< 5 min)\n"
         "• All 6 agent domains operational with Telegram command interface\n"
         "• Board-ready financial model for CAA Evolution process\n"
         "• Monthly close cycle reduced from days to hours"],
    ]

    t2 = Table(milestone_data, colWidths=[1.1 * inch, 0.8 * inch, 4.6 * inch], repeatRows=1)
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("LEADING", (0, 1), (-1, -1), 11),
        ("TEXTCOLOR", (0, 1), (-1, -1), DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t2)

    # --- The Demo ---
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("The Demo", s["section"]))
    elements.append(Paragraph(
        "The prototype dashboard you just saw is running against <b>real Dhar Mann Studios "
        "YouTube data</b> — your actual videos, view counts, and subscriber metrics — "
        "combined with realistic mock financial data structured for Sage Intacct. "
        "On Day 1, I swap in real Intacct credentials and the command center goes live.",
        s["body"],
    ))
    elements.append(Spacer(1, 6))

    demo_features = [
        ["Feature", "Status"],
        ["YouTube Data API integration (live DMS data)", "✅ Built"],
        ["Sage Intacct XML API client (mock mode)", "✅ Built"],
        ["5 dashboard views (Streamlit)", "✅ Built"],
        ["5 production agents with scheduling", "✅ Built"],
        ["Telegram notification system", "✅ Built"],
        ["FastAPI runtime with health checks", "✅ Built"],
        ["PDF/Excel investor report generation", "✅ Built"],
        ["50 automated tests passing", "✅ Verified"],
    ]
    t3 = Table(demo_features, colWidths=[4.5 * inch, 1.2 * inch])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEADING", (0, 0), (-1, -1), 12),
        ("TEXTCOLOR", (0, 1), (-1, -1), DARK),
        ("TEXTCOLOR", (1, 1), (1, -1), colors.HexColor("#2A9D8F")),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t3)

    # --- Footer ---
    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(
        width="100%", thickness=1, color=TEAL,
        spaceAfter=8, spaceBefore=0,
    ))
    elements.append(Paragraph(
        "Jake Pilcher  |  CFO &amp; Financial Systems Architect  |  "
        "Multi-entity finance + AI-powered automation",
        s["footer"],
    ))
    elements.append(Paragraph(
        "Built with Python, Sage Intacct API, YouTube Data API, Claude Sonnet 4, "
        "Streamlit, FastAPI, PostgreSQL",
        s["footer"],
    ))

    # Build PDF
    doc.build(elements)
    logger.info(f"Executive summary generated: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    path = generate_executive_summary()
    logger.info(f"PDF saved to: {path}")
    logger.info(f"Size: {path.stat().st_size:,} bytes")
