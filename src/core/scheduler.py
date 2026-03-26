"""Agent scheduler — APScheduler-based cron for all agent tasks."""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from src.core.config import get_settings


class AgentScheduler:
    """Manages scheduled execution of all agent tasks."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler(
            timezone=self.settings.SCHEDULER_TIMEZONE,
        )
        self._registered: list[str] = []

    def register_daily(
        self, name: str, func, hour: int = 7, minute: int = 0  # type: ignore[type-arg]
    ) -> None:
        """Register a daily task (default 7:00 AM PT)."""
        self.scheduler.add_job(
            func,
            CronTrigger(hour=hour, minute=minute),
            id=name,
            name=name,
            replace_existing=True,
        )
        self._registered.append(name)
        logger.info(f"Scheduled daily: {name} at {hour:02d}:{minute:02d}")

    def register_weekly(
        self, name: str, func, day_of_week: str = "mon", hour: int = 8  # type: ignore[type-arg]
    ) -> None:
        """Register a weekly task."""
        self.scheduler.add_job(
            func,
            CronTrigger(day_of_week=day_of_week, hour=hour),
            id=name,
            name=name,
            replace_existing=True,
        )
        self._registered.append(name)
        logger.info(f"Scheduled weekly: {name} on {day_of_week} at {hour:02d}:00")

    def register_monthly(
        self, name: str, func, day: int = 1, hour: int = 9  # type: ignore[type-arg]
    ) -> None:
        """Register a monthly task."""
        self.scheduler.add_job(
            func,
            CronTrigger(day=day, hour=hour),
            id=name,
            name=name,
            replace_existing=True,
        )
        self._registered.append(name)
        logger.info(f"Scheduled monthly: {name} on day {day} at {hour:02d}:00")

    def start(self) -> None:
        """Start the scheduler."""
        self.scheduler.start()
        logger.info(f"Scheduler started with {len(self._registered)} jobs")

    def stop(self) -> None:
        """Shut down the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    def get_status(self) -> list[dict]:
        """Get status of all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else "paused",
                "trigger": str(job.trigger),
            })
        return jobs
