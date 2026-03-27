"""FastAPI application — health checks, agent endpoints, Telegram webhook.

Run: uvicorn src.api.main:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from loguru import logger
from pydantic import BaseModel, Field

from src.agents.cash_forecast.agent import CashForecastAgent
from src.agents.concentration.agent import ConcentrationMonitorAgent
from src.agents.content_roi.agent import ContentROIAgent
from src.agents.investor_report.agent import InvestorReportAgent
from src.agents.platform_recon.agent import PlatformReconAgent
from src.core.config import get_settings
from src.core.scheduler import AgentScheduler

# ---------------------------------------------------------------------------
# Structured logging setup
# ---------------------------------------------------------------------------

settings = get_settings()

if not settings.DEBUG:
    logger.remove()
    logger.add(
        sys.stderr,
        format="{message}",
        serialize=True,
        level=settings.LOG_LEVEL,
    )

# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

scheduler = AgentScheduler()


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle."""
    logger.info("Starting Jake-DMS agent runtime")

    for warning in settings.validate_for_production():
        logger.warning(f"CONFIG: {warning}")

    recon = PlatformReconAgent()
    cash = CashForecastAgent()
    roi = ContentROIAgent()
    concentration = ConcentrationMonitorAgent()
    investor = InvestorReportAgent()

    scheduler.register_daily("platform_recon", recon.run_daily, hour=7)
    scheduler.register_daily("cash_forecast", cash.run_daily, hour=7, minute=15)
    scheduler.register_weekly("content_roi_weekly", roi.run_weekly, day_of_week="mon", hour=8)
    scheduler.register_monthly("content_roi_monthly", roi.run_monthly, day=1, hour=9)
    scheduler.register_monthly("concentration_monitor", concentration.run_monthly, day=5, hour=9)
    scheduler.register_monthly("investor_report", investor.generate, day=5, hour=10)

    scheduler.start()
    logger.info("Agent scheduler started")

    yield

    scheduler.stop()
    logger.info("Jake-DMS agent runtime stopped")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Jake-DMS Agent API",
    description="CFO Command Center Agent Runtime",
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

allowed_origins = (
    [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    if settings.CORS_ORIGINS
    else []
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API Key Auth
# ---------------------------------------------------------------------------

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str:
    """Validate the API key from header. Skip if no key configured."""
    if not settings.API_KEY:
        return "no-auth"
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key


# ---------------------------------------------------------------------------
# Health (public)
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "service": "jake-dms",
        "demo_mode": settings.DEMO_MODE,
    }


@app.get("/status")
async def status() -> dict:
    return {
        "scheduler_jobs": scheduler.get_status(),
        "demo_mode": settings.DEMO_MODE,
    }


# ---------------------------------------------------------------------------
# Agent Trigger Endpoints (auth-protected)
# ---------------------------------------------------------------------------

class TriggerResponse(BaseModel):
    status: str
    message: str


class GenerateReportRequest(BaseModel):
    period: str | None = Field(
        None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Period in YYYY-MM format (e.g. 2026-03)",
    )


@app.post("/agents/recon/run", response_model=TriggerResponse)
async def trigger_recon(
    background_tasks: BackgroundTasks,
    _key: str = Depends(verify_api_key),
) -> TriggerResponse:
    """Manually trigger platform reconciliation."""
    agent = PlatformReconAgent()
    background_tasks.add_task(agent.run_daily)
    return TriggerResponse(status="started", message="Platform reconciliation triggered")


@app.post("/agents/cash/run", response_model=TriggerResponse)
async def trigger_cash(
    background_tasks: BackgroundTasks,
    _key: str = Depends(verify_api_key),
) -> TriggerResponse:
    """Manually trigger cash forecast."""
    agent = CashForecastAgent()
    background_tasks.add_task(agent.run_daily)
    return TriggerResponse(status="started", message="Cash forecast triggered")


@app.post("/agents/roi/run", response_model=TriggerResponse)
async def trigger_roi(
    background_tasks: BackgroundTasks,
    _key: str = Depends(verify_api_key),
) -> TriggerResponse:
    """Manually trigger content ROI analysis."""
    agent = ContentROIAgent()
    background_tasks.add_task(agent.run_weekly)
    return TriggerResponse(status="started", message="Content ROI analysis triggered")


@app.post("/agents/concentration/run", response_model=TriggerResponse)
async def trigger_concentration(
    background_tasks: BackgroundTasks,
    _key: str = Depends(verify_api_key),
) -> TriggerResponse:
    """Manually trigger concentration analysis."""
    agent = ConcentrationMonitorAgent()
    background_tasks.add_task(agent.run_monthly)
    return TriggerResponse(status="started", message="Concentration analysis triggered")


@app.post("/agents/report/generate", response_model=TriggerResponse)
async def trigger_report(
    background_tasks: BackgroundTasks,
    request: GenerateReportRequest | None = None,
    _key: str = Depends(verify_api_key),
) -> TriggerResponse:
    """Manually trigger investor report generation."""
    period = request.period if request else None
    agent = InvestorReportAgent()
    background_tasks.add_task(agent.generate, period)
    return TriggerResponse(
        status="started",
        message=f"Investor report generation triggered for {period or 'current month'}",
    )
