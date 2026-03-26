# Jake-DMS — CFO Command Center

**AI-powered financial intelligence for Dhar Mann Studios** ($78M creator-led media company).

Built as a pre-interview prototype demonstrating what a modern CFO operating system looks like — real YouTube data, Sage Intacct integration-ready, 52 automated tests passing.

---

## The Pitch

> I don't just fill the CFO seat — I install a **financial operating system**. This prototype runs against actual DMS YouTube data combined with realistic Intacct-structured financials. On Day 1, I swap in real credentials and the command center goes live.

---

## Architecture

```
jake-dms/
├── src/
│   ├── agents/                  # 5 autonomous agent domains
│   │   ├── platform_recon/      # YouTube/Meta vs Intacct GL reconciliation
│   │   ├── content_roi/         # Episode-level profitability (cost → views → ROI)
│   │   ├── cash_forecast/       # 13-week rolling cash flow projection
│   │   ├── concentration/       # Revenue concentration monitor (HHI + alerts)
│   │   └── investor_report/     # Auto-generated investor packages (PDF + Excel)
│   ├── core/                    # Shared infrastructure
│   │   ├── config.py            # pydantic-settings (all config via env vars)
│   │   ├── intacct_client.py    # Sage Intacct XML API (async, retry, mock mode)
│   │   ├── youtube_analytics.py # YouTube Analytics OAuth2 (actual revenue)
│   │   ├── meta_client.py       # Meta Graph API for Facebook revenue
│   │   ├── telegram_bot.py      # Telegram notifications + commands
│   │   └── scheduler.py         # APScheduler cron for all agent tasks
│   ├── db/                      # SQLAlchemy ORM (SQLite demo / Postgres prod)
│   ├── demo/                    # Streamlit dashboard (5 pages)
│   │   ├── app.py               # Entry point
│   │   └── pages/               # Command Center, Content ROI, Recon, Cash, Investor
│   ├── api/                     # FastAPI runtime (health, agent triggers)
│   └── executive_summary.py     # 2-page PDF leave-behind generator
├── tests/                       # 52 tests (pytest + pytest-asyncio)
├── data/                        # Cached YouTube responses + generated reports
└── docker-compose.yml           # Postgres + app (production deployment)
```

---

## Agent Domains

| Domain | Schedule | What It Does |
|--------|----------|-------------|
| **Platform Revenue Recon** | Daily 7am PT | Reconciles YouTube/Meta estimated revenue against Intacct GL. Flags variances > 5%. |
| **Content ROI Engine** | Weekly Mon 8am | Maps Intacct project costs to YouTube performance. Cost per view by format, crew, series. |
| **Cash & Treasury** | Daily 7:15am | 13-week rolling forecast: platform payouts, brand deals, payroll, production spend. |
| **Concentration Monitor** | Monthly 5th | Tracks platform vs non-platform mix against 40% target. Herfindahl index. |
| **Investor Reporting** | Monthly 5th | Auto-generates board-ready packages (PDF + Excel) in < 5 minutes. |

All agents send Telegram summaries. All have mock mode for offline demo.

---

## Quick Start

```bash
# Install
poetry install

# Copy environment and add your YouTube API key
cp .env.example .env
# Edit .env → YOUTUBE_API_KEY=your_key_here

# Run the dashboard
poetry run streamlit run src/demo/app.py

# Run the API server
poetry run uvicorn src.api.main:app --host 0.0.0.0 --port 8080

# Generate the executive summary PDF
poetry run python -m src.executive_summary

# Run tests
poetry run pytest
```

---

## Dashboard Pages

1. **Command Center** — TTM revenue, operating margin, cash position, YouTube subscribers, AR aging, revenue by platform/business line, agent status panel
2. **Content ROI** — Production cost vs. revenue scatter plot, cost per 1K views by format, top/bottom 5 by ROI, full video table with adjustable CPM
3. **Reconciliation** — Estimated vs. actual revenue by period, variance by platform with 5% threshold lines, full recon detail + AR aging
4. **Cash Flow** — 13-week projection with minimum cash threshold, weekly inflows by source, outflows by category, week-by-week detail
5. **Investor Package** — P&L summary, COGS + OpEx breakdowns, revenue diversification donut, key ratios, YouTube metrics, CSV export

---

## Demo Mode

`DEMO_MODE=true` (default) uses:
- **SQLite** seeded with 18 months of realistic DMS financial data ($78M revenue, $58M expenses, 26% margin)
- **50 video production costs** across 5 formats (Long-Form, Short, Kids, Branded, Vertical)
- **YouTube Data API v3** for live channel stats (with disk cache fallback)
- **Mock Intacct responses** matching real API structure

Set `DEMO_MODE=false` + real credentials for production.

---

## Stack

Python 3.11 | Pydantic v2 | SQLAlchemy 2.0 | Streamlit | FastAPI | Plotly | httpx | loguru | APScheduler | ReportLab | Telegram Bot API

---

## Key Numbers (Mock Data)

| Metric | Value |
|--------|-------|
| Annual Revenue | $78M |
| Annual Expenses | $58M |
| Operating Margin | ~26% |
| Cash Position | $10.4M |
| Total AR | $8.2M |
| Videos Tracked | 50 |
| Revenue Sources | 6 platforms |
| GL Accounts | 35 |
| Historical Periods | 18 months |

---

*Built by Jake Pilcher — CFO & Financial Systems Architect*
