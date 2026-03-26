"""FastAPI application — health checks, agent endpoints, Telegram webhook.

Run: uvicorn src.api.main:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

from datetime import date

from fastapi import FastAPI, BackgroundTasks
from loguru import logger
from pydantic import BaseModel

from src.agents.cash_forecast.agent import CashForecastAgent
from src.agents.concentration.agent import ConcentrationMonitorAgent
from src.agents.content_roi.agent import ContentROIAgent
from src.agents.investor_report.agent import InvestorReportAgent
from src.agents.platform_recon.agent import PlatformReconAgent
from src.core.config import get_settings
from src.core.scheduler import AgentScheduler

app = FastAPI(
    title="Jake-DMS Agent API",
    description="CFO Command Center Agent Runtime",
    version="0.1.0",
)

scheduler = AgentScheduler()


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup() -> None:
    logger.info("Starting Jake-DMS agent runtime")

    # Register scheduled tasks
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


@app.on_event("shutdown")
async def shutdown() -> None:
    scheduler.stop()
    logger.info("Jake-DMS agent runtime stopped")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "service": "jake-dms",
        "demo_mode": get_settings().DEMO_MODE,
    }


@app.get("/status")
async def status() -> dict:
    return {
        "scheduler_jobs": scheduler.get_status(),
        "demo_mode": get_settings().DEMO_MODE,
    }


# ---------------------------------------------------------------------------
# Agent Trigger Endpoints
# ---------------------------------------------------------------------------

class TriggerResponse(BaseModel):
    status: str
    message: str


@app.post("/agents/recon/run", response_model=TriggerResponse)
async def trigger_recon(background_tasks: BackgroundTasks) -> TriggerResponse:
    """Manually trigger platform reconciliation."""
    agent = PlatformReconAgent()
    background_tasks.add_task(agent.run_daily)
    return TriggerResponse(status="started", message="Platform reconciliation triggered")


@app.post("/agents/cash/run", response_model=TriggerResponse)
async def trigger_cash(background_tasks: BackgroundTasks) -> TriggerResponse:
    """Manually trigger cash forecast."""
    agent = CashForecastAgent()
    background_tasks.add_task(agent.run_daily)
    return TriggerResponse(status="started", message="Cash forecast triggered")


@app.post("/agents/roi/run", response_model=TriggerResponse)
async def trigger_roi(background_tasks: BackgroundTasks) -> TriggerResponse:
    """Manually trigger content ROI analysis."""
    agent = ContentROIAgent()
    background_tasks.add_task(agent.run_weekly)
    return TriggerResponse(status="started", message="Content ROI analysis triggered")


@app.post("/agents/concentration/run", response_model=TriggerResponse)
async def trigger_concentration(background_tasks: BackgroundTasks) -> TriggerResponse:
    """Manually trigger concentration analysis."""
    agent = ConcentrationMonitorAgent()
    background_tasks.add_task(agent.run_monthly)
    return TriggerResponse(status="started", message="Concentration analysis triggered")


@app.post("/agents/report/generate", response_model=TriggerResponse)
async def trigger_report(
    background_tasks: BackgroundTasks, period: str | None = None
) -> TriggerResponse:
    """Manually trigger investor report generation."""
    agent = InvestorReportAgent()
    background_tasks.add_task(agent.generate, period)
    return TriggerResponse(
        status="started",
        message=f"Investor report generation triggered for {period or 'current month'}",
    )
