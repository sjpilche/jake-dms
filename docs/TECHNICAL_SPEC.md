# Jake-DMS Technical Specification
## CFO Command Center for Dhar Mann Studios

**Version:** 0.1.0 (Build 1 — Pre-Interview Demo)
**Author:** Jake Pilcher
**Date:** March 26, 2026
**Status:** 52 tests passing, Streamlit Cloud deployed, all agents operational in mock mode

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Architecture](#3-architecture)
4. [Data Model](#4-data-model)
5. [Agent Domains](#5-agent-domains)
6. [Dashboard Pages](#6-dashboard-pages)
7. [API Endpoints](#7-api-endpoints)
8. [External Integrations](#8-external-integrations)
9. [Configuration](#9-configuration)
10. [Testing](#10-testing)
11. [Deployment](#11-deployment)
12. [File Inventory](#12-file-inventory)
13. [Roadmap](#13-roadmap)

---

## 1. Project Overview

### Purpose
AI-powered CFO command center purpose-built for Dhar Mann Studios, a $78M/yr creator-led media company. Automates platform revenue reconciliation, content ROI tracking, cash flow forecasting, revenue concentration monitoring, and investor reporting.

### Build Phases
| Phase | Description | Status |
|-------|-------------|--------|
| **Build 1** | Pre-interview demo — mock Intacct data + live YouTube API | Complete |
| **Build 2** | Production agents — real Intacct credentials, Telegram commands, scheduled runs | Planned |
| **Build 3** | Executive summary — 2-page PDF leave-behind for interview | Complete |

### Key Design Principles
- **No print()** — all logging via `loguru`
- **Pydantic v2 strict mode** on every model
- **Type hints** on every function signature
- **Decimal for financial math** — never float for money, never LLM-generated
- **Mock mode on every external dependency** — controlled by env var
- **Fail loudly** — raise, don't swallow; log the error, then raise
- **Tests for every calculation** — no test, no merge

---

## 2. Technology Stack

### Core
| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11+ |
| Package Manager | Poetry | latest |
| Models / Validation | Pydantic v2 | ^2.0 |
| Configuration | pydantic-settings | ^2.0 |
| ORM | SQLAlchemy | ^2.0 |
| HTTP Client | httpx | ^0.27 |
| Logging | loguru | ^0.7 |

### Frontend / Visualization
| Component | Technology | Version |
|-----------|-----------|---------|
| Dashboard | Streamlit | ^1.40 |
| Charts | Plotly | ^5.24 |
| Data Tables | pandas | ^2.0 |

### Backend / Runtime
| Component | Technology | Version |
|-----------|-----------|---------|
| API Server | FastAPI | ^0.115 |
| ASGI Server | uvicorn | ^0.34 |
| Task Scheduler | APScheduler | ^3.10 |
| Notifications | Telegram Bot API (httpx) | — |

### Data / Reports
| Component | Technology | Version |
|-----------|-----------|---------|
| Demo Database | SQLite | built-in |
| Production Database | PostgreSQL (via asyncpg) | ^0.30 |
| PDF Generation | ReportLab | ^4.0 |
| Excel Generation | openpyxl | ^3.1 |
| XML Parsing | xmltodict | ^0.14 |

### External APIs
| API | Auth | Purpose |
|-----|------|---------|
| YouTube Data API v3 | API Key | Public channel stats, video metrics |
| YouTube Analytics API | OAuth2 | Actual revenue, CPM, watch time |
| Meta Graph API | Access Token | Facebook page views, estimated revenue |
| Sage Intacct XML API | Sender/Company/User credentials | GL, AR, AP, Cash, Projects, Rev Rec |
| Telegram Bot API | Bot Token | Agent notifications + command interface |

### Dev Tools
| Tool | Purpose |
|------|---------|
| pytest + pytest-asyncio | Test runner |
| mypy (strict) | Static type checking |
| ruff | Linting (E, F, I, N, W rules) |

---

## 3. Architecture

### High-Level
```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                    │
│  (5 pages: Command Center, ROI, Recon, Cash, Investor)  │
└─────────────────────┬───────────────────────────────────┘
                      │ reads from
┌─────────────────────▼───────────────────────────────────┐
│                  SQLite / PostgreSQL                      │
│  (GL, AR, AP, Cash, Production Costs, P&L, Recon, etc.) │
└─────────────────────▲───────────────────────────────────┘
                      │ writes to
┌─────────────────────┴───────────────────────────────────┐
│                 5 Autonomous Agents                       │
│  Platform Recon │ Content ROI │ Cash │ Conc. │ Investor  │
└──────┬──────────┬─────────────┬──────┬───────┬──────────┘
       │          │             │      │       │
  ┌────▼────┐ ┌──▼──┐ ┌───────▼──┐ ┌─▼──┐ ┌──▼──────┐
  │ YouTube │ │Meta │ │ Intacct  │ │Tele│ │ReportLab│
  │ API v3  │ │Graph│ │ XML API  │ │gram│ │+ openpyxl│
  └─────────┘ └─────┘ └──────────┘ └────┘ └─────────┘
```

### Request Flow
1. **Streamlit pages** call `@st.cache_data` functions that query the SQLite DB
2. **YouTube public client** fetches live channel/video data (cached to disk)
3. **Agents** run on APScheduler cron jobs via the FastAPI runtime
4. **Agents** pull from external APIs (YouTube Analytics, Meta, Intacct)
5. **Agents** write results to DB + send Telegram notifications
6. **Reports** generated as PDF/Excel on demand or monthly schedule

### Module Dependency Graph
```
src/core/config.py          ← everything reads this
src/core/models.py          ← shared Pydantic domain models
src/db/models.py            ← SQLAlchemy ORM (mirrors core/models.py)
src/db/engine.py            ← session factory, init_db()
src/core/intacct_client.py  ← agents use this
src/core/youtube_analytics.py ← agents use this
src/core/meta_client.py     ← agents use this
src/core/telegram_bot.py    ← agents use this
src/core/scheduler.py       ← api/main.py uses this
src/agents/*/agent.py       ← business logic
src/agents/*/models.py      ← agent-specific Pydantic models
src/demo/mock_data.py       ← seeds SQLite for demo
src/demo/youtube_public.py  ← Streamlit pages use this
src/demo/theme.py           ← Streamlit UI components
src/demo/app.py             ← Streamlit entry point
src/demo/pages/*.py         ← 5 dashboard pages
src/api/main.py             ← FastAPI runtime
src/executive_summary.py    ← PDF generator (standalone)
```

---

## 4. Data Model

### SQLAlchemy ORM Tables

| Table | Rows (Demo) | Description |
|-------|-------------|-------------|
| `gl_accounts` | 35 | Chart of accounts (Revenue 4xxx, COGS 5xxx, OpEx 6xxx, Assets 1xxx, Liabilities 2xxx, Equity 3xxx) |
| `gl_balances` | ~400 | Monthly debit/credit/net by account (18 months × 22 accounts) |
| `pl_items` | ~1,600 | P&L line items by category/subcategory/business_line/period |
| `platform_revenue` | ~108 | Revenue by platform/business_line/period (ad, sponsorship, licensing splits) |
| `ar_aging` | 13 | Accounts receivable by customer with aging buckets (Current, 30, 60, 90+) |
| `ap_aging` | 10 | Accounts payable by vendor with aging buckets |
| `cash_balances` | 4 | Bank accounts (Operating, Payroll, Reserve, Escrow) |
| `production_costs` | 50 | Per-video costs (talent, crew, location, post, music) by format/crew |
| `recon_records` | ~12 | Platform reconciliation records (estimated vs actual, variance, status) |

### Pydantic Domain Models (src/core/models.py)

**Enums:**
- `BusinessLine` — Core Content, 5th Quarter, Brand Deals, Licensing/OTT, Merchandise, Other
- `Platform` — YouTube, Facebook, TikTok, Snap, Licensing, Other
- `ContentFormat` — Long-Form, Short, Kids Series, Branded, Vertical
- `AgingBucket` — Current, 1-30 Days, 31-60 Days, 61-90 Days, 90+ Days

**Financial Models:** GLAccount, GLBalance, ARAgingRecord, CashPosition, ProductionCost, PlatformRevenue, PLLineItem, ReconRecord

**YouTube Models:** YouTubeChannel, YouTubeVideo

**Composite Models:** ContentROI, CashFlowWeek

### Mock Data Constants
- **Annual Revenue:** $78M (YouTube $32M, Brand Deals $18M, Licensing $12M, Facebook $8M, Merch $5M, Other $3M)
- **Annual Expenses:** $58M (Salaries $14M, Talent $8.5M, Crew $6.2M, Marketing $6M, G&A $5M, etc.)
- **Operating Margin:** ~26%
- **Seasonal Multipliers:** Q1=0.85, Q2=0.95, Q3=1.0, Q4=1.20
- **RNG Seed:** 42 (deterministic, reproducible)
- **Cash Accounts:** JPMorgan Operating ($4.2M), JPMorgan Payroll ($1.8M), First Republic Reserve ($3.5M), City National Escrow ($814K)

---

## 5. Agent Domains

### Agent 1: Platform Revenue Reconciliation
**File:** `src/agents/platform_recon/agent.py`
**Schedule:** Daily at 7:00 AM PT
**Flow:**
1. Pull estimated revenue from YouTube Analytics API + Meta Graph API
2. Pull actual GL deposits from Intacct (GLENTRY)
3. Match platform → vendor and calculate variance
4. Flag items with variance > 5%
5. Write flagged items to Intacct statistical journal (RECON)
6. Send Telegram summary (matched count, flagged count, details)

**Models:** PlatformEstimate, GLDeposit, ReconResult

### Agent 2: Content ROI Engine
**File:** `src/agents/content_roi/agent.py`
**Schedule:** Weekly Monday 8:00 AM PT, Monthly 1st 9:00 AM PT
**Flow (weekly):**
1. Get production costs from Intacct project accounting (APBILL)
2. Get YouTube video performance (views, publish date)
3. Calculate per-episode: CPM revenue estimate, cost/view, cost/1K views, margin, ROI
4. Sort and extract top/bottom 5
5. Send Telegram weekly ROI report

**Flow (monthly):**
1. Aggregate episodes by content format
2. Calculate format-level margin analysis
3. Push avg ROI per format to Intacct statistical accounts

**Models:** EpisodeMapping, EpisodeROI, FormatMarginReport

### Agent 3: Cash & Treasury Forecast
**File:** `src/agents/cash_forecast/agent.py`
**Schedule:** Daily at 7:15 AM PT
**Flow:**
1. Get current cash balances from Intacct (CHECKINGACCOUNT)
2. Project AR collections by week from aging buckets
3. Build 13-week forecast incorporating:
   - Platform payout schedules (Google pays ~21st, 45-day lag)
   - Brand deal payment terms
   - Biweekly payroll ($538K/cycle)
   - Production spend, facilities, tech, marketing, G&A
4. Check alerts: flag any week where projected cash < 2× weekly burn
5. Send Telegram daily cash position + 4-week forward view
6. Send alert messages for any below-minimum weeks

**Models:** WeeklyForecast, CashAlert

### Agent 4: Revenue Concentration Monitor
**File:** `src/agents/concentration/agent.py`
**Schedule:** Monthly on 5th at 9:00 AM PT
**Flow:**
1. Get revenue by source from Intacct GL (dimension-tagged)
2. Classify sources as platform (YouTube, Facebook, TikTok, Snap) vs non-platform
3. Calculate: platform %, non-platform %, Herfindahl index (HHI), largest single source %
4. Evaluate alert levels: GREEN (<40%), YELLOW (40-50%), RED (>50%)
5. Send Telegram concentration alert if YELLOW or RED

**Models:** ConcentrationMetrics, ConcentrationAlert

**Herfindahl Index:** Sum of squared market shares (0-10,000). 10,000 = single source monopoly. DMS target: below 2,500.

### Agent 5: Investor Reporting
**File:** `src/agents/investor_report/agent.py`
**Schedule:** Monthly on 5th at 10:00 AM PT
**Flow:**
1. Assemble data from Intacct: revenue by biz line, revenue by platform, COGS, OpEx, cash, AR
2. Get YouTube channel metrics (subscribers, views)
3. Calculate: gross margin, operating margin, platform concentration
4. Generate Excel workbook (3 sheets: Summary, Revenue by Biz Line, Revenue by Platform)
5. Generate PDF report (P&L summary table, key metrics table, teal branding)
6. Send Telegram notification with key metrics

**Models:** InvestorPackage, ReportOutput

**Output files:** `data/reports/investor_package_{period}.xlsx`, `data/reports/investor_package_{period}.pdf`

---

## 6. Dashboard Pages

### Landing Page (app.py)
- Centered hero: "DMS CFO Command Center" with PROTOTYPE DEMO badge
- Quick stats: 6 Agent Domains, 18 Specialist Agents, 5 Dashboard Views, Real-Time YouTube Data
- Navigation instructions

### Page 1: Command Center (01_command_center.py)
**KPIs:** TTM Revenue, Operating Margin, Cash Position, YouTube Subscribers
**Charts:**
- Monthly Revenue Trend (line: revenue vs expenses, 18 months)
- Revenue by Platform (donut: YouTube, Facebook, Brand Deals, Licensing, Merch, Other)
- AR Aging Summary (stacked bar by customer: Current, 30, 60, 90+ days)
- Revenue by Business Line TTM (bar: Core Content, 5th Quarter, Brand Deals, etc.)
**Tables:** Agent Status Panel (6 domains with status + latest activity)

### Page 2: Content ROI (02_content_roi.py)
**Controls:** CPM Assumption slider (sidebar, $2.00–$8.00, default $4.50)
**KPIs:** Avg Production Cost, Avg Revenue/Video, Avg ROI, Videos Analyzed
**Charts:**
- Production Cost vs. Revenue (scatter: sized by views, colored by format, breakeven line)
- Avg Cost/1K Views by Format (bar)
**Tables:** Top 5 by ROI, Bottom 5 by ROI, Full Video ROI Table (sortable, 50 rows)

### Page 3: Reconciliation (03_reconciliation.py)
**KPIs:** Total Estimated Revenue, Total Received, Net Variance (with over/under indicator), Flagged Items
**Charts:**
- Reconciliation by Period (grouped bar: estimated vs actual, 6 months)
- Variance by Platform (bar with ±5% threshold lines)
**Tables:** Reconciliation Detail (period, platform, estimated, actual, variance, status), AR Aging Detail
**Callout:** AR summary with total over 60 days and percentage

### Page 4: Cash Flow (04_cash_flow.py)
**KPIs:** Current Cash, Projected 13-Wk Low (with minimum threshold check), Avg Weekly Outflow, Weeks of Runway
**Charts:**
- 13-Week Cash Projection (area chart with minimum cash threshold line)
- Weekly Inflows by Source (stacked bar: Platform Payouts, Brand Deals, Licensing, Other)
- Weekly Outflows by Category (stacked bar: Payroll, Production, Talent, Facilities, Tech, Marketing, G&A)
**Tables:** Week-by-Week Detail (opening cash, inflows, outflows, net change, closing cash)

### Page 5: Investor Package (05_investor_package.py)
**KPIs:** Total Revenue (18mo), Gross Margin, Operating Margin, Platform Concentration (with target indicator)
**Charts:**
- Revenue Diversification (donut by platform with color-coded threshold alerts)
- Revenue by Business Line Monthly Trend (stacked bar, 18 months)
**Tables:** P&L Summary (Revenue → COGS → Gross Profit → OpEx → Operating Income), COGS Breakdown, OpEx Breakdown
**Key Ratios Panel:** Gross Margin, Operating Margin, Cash Position, Total AR, Revenue/Employee, Largest Single Source
**YouTube Metrics:** Subscribers, Total Views, Total Videos (live if API key set)
**Export:** Download Summary as CSV button

---

## 7. API Endpoints

**Base URL:** `http://localhost:8080`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (status, service name, demo_mode) |
| GET | `/status` | Scheduler job status (all registered jobs with next_run) |
| POST | `/agents/recon/run` | Trigger platform reconciliation (background task) |
| POST | `/agents/cash/run` | Trigger cash forecast (background task) |
| POST | `/agents/roi/run` | Trigger content ROI analysis (background task) |
| POST | `/agents/concentration/run` | Trigger concentration analysis (background task) |
| POST | `/agents/report/generate?period=YYYY-MM` | Trigger investor report (optional period param) |

All trigger endpoints return `{"status": "started", "message": "..."}` and execute the agent in the background.

---

## 8. External Integrations

### YouTube Data API v3 (src/demo/youtube_public.py)
- **Auth:** API Key (public data only)
- **Channel ID:** UC_hK9fOxyy_TM8FJGXIyG8Q (Dhar Mann Studios)
- **Endpoints used:** channels.list, search.list, videos.list
- **Caching:** Every response saved to `data/youtube_cache_{key}.json`
- **Fallback:** If no API key or API fails, reads from disk cache
- **Rate limit:** 10,000 quota units/day (free tier)

### YouTube Analytics API (src/core/youtube_analytics.py)
- **Auth:** OAuth2 (requires token file at `config/youtube_token.json`)
- **Endpoints used:** reports (daily metrics, geo breakdown)
- **Metrics:** views, estimatedRevenue, estimatedAdRevenue, cpm, averageViewDuration, subscribersGained
- **Mock mode:** Returns deterministic fake data when `DEMO_MODE=true`

### Meta Graph API (src/core/meta_client.py)
- **Auth:** Page Access Token
- **Endpoint:** `/{page_id}/insights`
- **Metrics:** page_views_total, page_impressions, page_post_engagements
- **Mock mode:** Returns deterministic daily metrics when `DEMO_MODE=true`

### Sage Intacct XML API (src/core/intacct_client.py)
- **Auth:** Sender ID/Password + Company ID + User ID/Password
- **Endpoint:** `https://api.intacct.com/ia/xml/xmlgw.phtml`
- **Operations:** readByQuery, readReport, create
- **Objects queried:** CHECKINGACCOUNT, ARINVOICE, GLENTRY, APBILL, REVRECSCHEDULE
- **Features:** Retry logic (3 attempts, exponential backoff), pagination (1000/page), XML envelope builder, error parser
- **Mock mode:** Returns hardcoded demo data matching real API structure when `INTACCT_MOCK_MODE=true`

### Telegram Bot API (src/core/telegram_bot.py)
- **Auth:** Bot Token + Chat ID
- **Method:** sendMessage (HTML parse mode)
- **Notification types:**
  - Daily cash position (total + 4-week forward view with red/green indicators)
  - Reconciliation summary (matched/flagged counts, variance details)
  - Content ROI weekly report (top 5 / bottom 5 by ROI)
  - Concentration alert (RED/YELLOW/GREEN with platform % and largest source)
  - Investor package ready (period, revenue, margin, file count)
- **Mock mode:** Logs messages when no token configured

---

## 9. Configuration

### Environment Variables (src/core/config.py)

All config via pydantic-settings `BaseSettings`. Reads from `.env` file or environment variables.

| Variable | Default | Description |
|----------|---------|-------------|
| `YOUTUBE_API_KEY` | `""` | YouTube Data API v3 key |
| `YOUTUBE_CHANNEL_ID` | `UC_hK9fOxyy_TM8FJGXIyG8Q` | DMS channel |
| `YOUTUBE_OAUTH_CLIENT_ID` | `""` | OAuth2 client ID (Build 2) |
| `YOUTUBE_OAUTH_CLIENT_SECRET` | `""` | OAuth2 client secret (Build 2) |
| `YOUTUBE_OAUTH_TOKEN_PATH` | `config/youtube_token.json` | Stored OAuth token |
| `META_ACCESS_TOKEN` | `""` | Meta Graph API page token |
| `META_PAGE_ID` | `""` | Facebook page ID |
| `DATABASE_URL` | `sqlite:///./jake_dms.db` | Demo database |
| `POSTGRES_URL` | `postgresql+asyncpg://jake:jake@localhost:5432/jake_dms` | Production DB |
| `DEMO_MODE` | `true` | Use mock data + cached responses |
| `DATA_DIR` | `<repo>/data` | Cache + report output directory |
| `LOG_LEVEL` | `INFO` | Loguru log level |
| `DEBUG` | `false` | SQLAlchemy echo + verbose logging |
| `INTACCT_SENDER_ID` | `""` | Intacct Web Services sender |
| `INTACCT_SENDER_PASSWORD` | `""` | Sender password |
| `INTACCT_COMPANY_ID` | `""` | Intacct company |
| `INTACCT_USER_ID` | `""` | Intacct user |
| `INTACCT_USER_PASSWORD` | `""` | Intacct user password |
| `INTACCT_ENDPOINT` | `https://api.intacct.com/ia/xml/xmlgw.phtml` | API endpoint |
| `INTACCT_MOCK_MODE` | `true` | Return mock data instead of calling API |
| `TELEGRAM_BOT_TOKEN` | `""` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | `""` | Target chat/group ID |
| `LLM_MODEL` | `claude-sonnet-4-20250514` | Claude model for future AI features |
| `LLM_API_KEY` | `""` | Anthropic API key |
| `SCHEDULER_TIMEZONE` | `America/Los_Angeles` | Agent schedule timezone |
| `API_HOST` | `0.0.0.0` | FastAPI bind address |
| `API_PORT` | `8080` | FastAPI port |

---

## 10. Testing

### Test Suite: 52 tests across 6 files

```
tests/
├── conftest.py              # Fixtures: demo env, in-memory DB session
├── test_mock_data.py        # 11 tests — data seeder validation
├── test_youtube_public.py   # 11 tests — duration parsing, CPM calc, cache fallback
├── test_agents.py           # 15 tests — all 5 agents in mock mode
├── test_api.py              #  7 tests — FastAPI health, status, all trigger endpoints
├── test_intacct_client.py   #  7 tests — mock reads, creates, envelope, error handling
└── test_executive_summary.py #  2 tests — PDF generation, multipage validation
```

### Key Test Categories

**Financial Calculations (test_mock_data.py):**
- Revenue approximately $78M annualized (within tolerance)
- Operating margin 10-40% range
- AR/AP aging rows sum correctly (buckets = total)
- Cash balances all positive, total > $8M
- Production cost components sum to total_cost
- 50 production cost records, 5+ platform coverage

**Agent Logic (test_agents.py):**
- Platform recon: run_daily returns 2 results (YouTube + Facebook), flags 20% variance, matches 2% variance
- Content ROI: mock costs/metrics return 50 items, format aggregation works
- Cash forecast: run_daily returns 13 weeks, below_minimum alerts fire correctly
- Concentration: monthly returns valid metrics, RED at 70% platform, GREEN at 20%, HHI=10000 for single source
- Investor report: generates package with valid margins, Excel output > 0 bytes, PDF output > 0 bytes

**API (test_api.py):**
- Health returns 200 with status=healthy
- Status returns scheduler_jobs
- All 5 trigger endpoints return 200 with status=started

### Running Tests
```bash
poetry run pytest                  # all tests
poetry run pytest -v               # verbose
poetry run pytest --tb=short       # short tracebacks
poetry run mypy src/               # type checking
```

---

## 11. Deployment

### Local Development
```bash
poetry install
cp .env.example .env
# Edit .env with your API keys
poetry run streamlit run src/demo/app.py          # Dashboard on :8501
poetry run uvicorn src.api.main:app --port 8080   # API on :8080
```

### Streamlit Community Cloud
- **Repo:** github.com/sjpilche/jake-dms (public)
- **Branch:** master
- **Entry point:** src/demo/app.py
- **Dependencies:** requirements.txt (exported from pyproject.toml)
- **Secrets:** Add YOUTUBE_API_KEY in Streamlit Cloud dashboard
- **URL:** assigned by Streamlit Cloud on deploy

### Docker Compose (Production)
```bash
docker compose up -d
```
Services:
- **postgres** — PostgreSQL 16 Alpine on :5432 (user: jake, db: jake_dms)
- **app** — FastAPI on :8080 + Streamlit on :8501, depends on postgres healthy

### Python Version
- **Required:** 3.11+
- **Tested on:** 3.11.9, 3.12.10

---

## 12. File Inventory

### Source Files (57 total)

```
src/
├── __init__.py
├── executive_summary.py              # 326 lines — 2-page PDF generator
├── agents/
│   ├── __init__.py
│   ├── cash_forecast/
│   │   ├── __init__.py
│   │   ├── agent.py                  # 193 lines — 13-week forecast
│   │   └── models.py                 #  44 lines — WeeklyForecast, CashAlert
│   ├── concentration/
│   │   ├── __init__.py
│   │   ├── agent.py                  # 167 lines — HHI + platform mix
│   │   └── models.py                 #  30 lines — ConcentrationMetrics, ConcentrationAlert
│   ├── content_roi/
│   │   ├── __init__.py
│   │   ├── agent.py                  # 232 lines — episode ROI + format margins
│   │   └── models.py                 #  55 lines — EpisodeROI, FormatMarginReport
│   ├── investor_report/
│   │   ├── __init__.py
│   │   ├── agent.py                  # 286 lines — PDF/Excel report gen
│   │   └── models.py                 #  42 lines — InvestorPackage, ReportOutput
│   └── platform_recon/
│       ├── __init__.py
│       ├── agent.py                  # 179 lines — recon + stat journals
│       └── models.py                 #  37 lines — PlatformEstimate, ReconResult
├── api/
│   ├── __init__.py
│   └── main.py                       # 136 lines — FastAPI + scheduler + triggers
├── core/
│   ├── __init__.py
│   ├── config.py                     #  71 lines — pydantic-settings
│   ├── intacct_client.py             # 306 lines — XML API + retry + mock
│   ├── meta_client.py                # 101 lines — Graph API + mock
│   ├── models.py                     # 209 lines — domain models + enums
│   ├── scheduler.py                  #  85 lines — APScheduler wrapper
│   ├── telegram_bot.py               # 139 lines — notifications
│   └── youtube_analytics.py          # 226 lines — OAuth2 + revenue data
├── db/
│   ├── __init__.py
│   ├── engine.py                     #  53 lines — SQLAlchemy session factory
│   └── models.py                     # 125 lines — ORM table definitions
└── demo/
    ├── __init__.py
    ├── app.py                        #  76 lines — Streamlit entry point
    ├── mock_data.py                  # 516 lines — data seeder
    ├── theme.py                      # 151 lines — colors + UI components
    ├── youtube_public.py             # 181 lines — Data API v3 + caching
    └── pages/
        ├── 01_command_center.py      # 253 lines
        ├── 02_content_roi.py         # 210 lines
        ├── 03_reconciliation.py      # 195 lines
        ├── 04_cash_flow.py           # 221 lines
        └── 05_investor_package.py    # 260 lines

tests/
├── __init__.py
├── conftest.py                       #  31 lines
├── test_agents.py                    # 159 lines — 15 tests
├── test_api.py                       #  53 lines — 7 tests
├── test_executive_summary.py         #  22 lines — 2 tests
├── test_intacct_client.py            #  57 lines — 7 tests
├── test_mock_data.py                 #  82 lines — 11 tests
└── test_youtube_public.py            #  56 lines — 11 tests
```

### Config Files
```
.env.example                          # Template for environment variables
.gitignore                            # Python, IDE, .env, *.db, caches
.streamlit/config.toml                # Theme (teal) + headless server
CLAUDE.md                             # AI agent development guidelines
README.md                             # Full project documentation
docker-compose.yml                    # Postgres + app services
pyproject.toml                        # Poetry config, dependencies, tool settings
requirements.txt                      # For Streamlit Cloud deployment
```

### Generated Files (gitignored)
```
jake_dms.db                           # SQLite demo database
poetry.lock                           # Dependency lock file
data/youtube_cache_*.json             # Cached YouTube API responses
data/reports/executive_summary.pdf    # 2-page leave-behind
data/reports/investor_package_*.xlsx  # Monthly Excel reports
data/reports/investor_package_*.pdf   # Monthly PDF reports
```

---

## 13. Roadmap

### Build 2: Production Agents (Post-Hire, Days 1-30)
- [ ] Real Sage Intacct credentials + connection validation
- [ ] Complete QuickBooks → Intacct chart of accounts migration
- [ ] YouTube Analytics OAuth2 flow (actual revenue data)
- [ ] Meta Business Suite production access
- [ ] Telegram bot with command interface (/status, /cash, /recon, /roi, /generate_report)
- [ ] PostgreSQL migration from SQLite
- [ ] Agent health monitoring + error recovery
- [ ] Migrate FastAPI from `on_event` to `lifespan` handlers

### Build 2.5: Intelligence Layer (Days 31-60)
- [ ] Content ROI engine live with real Intacct project codes
- [ ] 13-week cash forecast with actual bank feeds
- [ ] Revenue concentration dashboard with historical trend
- [ ] Brand deal pipeline tracking + ASC 606 rev rec automation
- [ ] Monthly close cycle automation

### Build 3: Scale (Days 61-100)
- [ ] Full 18-agent deployment across all 6 domains
- [ ] Board-ready financial model for CAA Evolution process
- [ ] Automated investor packages in < 5 minutes
- [ ] Claude AI integration for natural language financial queries
- [ ] Multi-entity consolidation (if applicable)

---

*Generated March 26, 2026 — Jake-DMS v0.1.0*
