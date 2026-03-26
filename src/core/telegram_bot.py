"""Telegram bot interface for agent notifications and commands.

Commands: /status, /cash, /recon, /roi, /generate_report
"""

from __future__ import annotations

from loguru import logger

from src.core.config import get_settings


class TelegramNotifier:
    """Send notifications via Telegram Bot API.

    Uses httpx directly (not python-telegram-bot) to keep it simple
    and async-compatible without the full framework.
    """

    BASE_URL = "https://api.telegram.org"

    def __init__(self) -> None:
        self.settings = get_settings()
        self._enabled = bool(
            self.settings.TELEGRAM_BOT_TOKEN and self.settings.TELEGRAM_CHAT_ID
        )
        if not self._enabled:
            logger.warning("Telegram not configured — notifications will be logged only")

    async def send_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        chat_id: str | None = None,
    ) -> bool:
        """Send a message to the configured Telegram chat."""
        target = chat_id or self.settings.TELEGRAM_CHAT_ID

        if not self._enabled:
            logger.info(f"[TELEGRAM-MOCK] → {target}: {text[:200]}")
            return True

        import httpx
        url = (
            f"{self.BASE_URL}/bot{self.settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        )
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json={
                    "chat_id": target,
                    "text": text,
                    "parse_mode": parse_mode,
                })
                resp.raise_for_status()
                logger.debug(f"Telegram message sent to {target}")
                return True
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    async def send_daily_cash_summary(
        self,
        total_cash: float,
        weekly_forecast: list[dict],
    ) -> bool:
        """Send formatted daily cash position summary."""
        lines = [
            "<b>💰 Daily Cash Position</b>",
            f"Total: <b>${total_cash:,.0f}</b>",
            "",
            "<b>4-Week Forward View:</b>",
        ]
        for week in weekly_forecast[:4]:
            flag = "🔴" if week.get("below_minimum") else "🟢"
            lines.append(
                f"  {flag} Wk {week['week']}: ${week['closing_cash']:,.0f}"
            )
        return await self.send_message("\n".join(lines))

    async def send_recon_summary(
        self,
        matched: int,
        flagged: int,
        total_variance: float,
        details: list[dict],
    ) -> bool:
        """Send reconciliation summary."""
        status = "✅" if flagged == 0 else "⚠️"
        lines = [
            f"<b>{status} Platform Reconciliation</b>",
            f"Matched: {matched} | Flagged: {flagged}",
            f"Net Variance: ${total_variance:+,.0f}",
        ]
        if details:
            lines.append("")
            lines.append("<b>Flagged Items:</b>")
            for d in details[:5]:
                lines.append(
                    f"  • {d['platform']} {d['period']}: "
                    f"${d['variance']:+,.0f} ({d['variance_pct']:+.1f}%)"
                )
        return await self.send_message("\n".join(lines))

    async def send_roi_summary(
        self,
        top_5: list[dict],
        bottom_5: list[dict],
    ) -> bool:
        """Send weekly content ROI summary."""
        lines = ["<b>📊 Weekly Content ROI Report</b>", "", "<b>Top 5:</b>"]
        for v in top_5:
            lines.append(f"  🏆 {v['title'][:40]}… ROI: {v['roi']:.0f}%")
        lines.append("")
        lines.append("<b>Bottom 5:</b>")
        for v in bottom_5:
            lines.append(f"  ⚠️ {v['title'][:40]}… ROI: {v['roi']:.0f}%")
        return await self.send_message("\n".join(lines))

    async def send_concentration_alert(
        self,
        platform_pct: float,
        largest_source: str,
        largest_pct: float,
    ) -> bool:
        """Send revenue concentration alert."""
        if platform_pct > 50:
            level = "🔴 RED ALERT"
        elif largest_pct > 30:
            level = "🟡 YELLOW"
        else:
            level = "🟢 OK"

        lines = [
            f"<b>{level} — Revenue Concentration</b>",
            f"Platform Revenue: <b>{platform_pct:.0f}%</b> (target: &lt;40%)",
            f"Largest Source: {largest_source} ({largest_pct:.0f}%)",
        ]
        return await self.send_message("\n".join(lines))
