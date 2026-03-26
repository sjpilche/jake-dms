"""Application configuration via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration — all values come from env vars or .env file."""

    # -- YouTube ---------------------------------------------------------------
    YOUTUBE_API_KEY: str = ""
    YOUTUBE_CHANNEL_ID: str = "UC_hK9fOxyy_TM8FJGXIyG8Q"
    YOUTUBE_OAUTH_CLIENT_ID: str = ""
    YOUTUBE_OAUTH_CLIENT_SECRET: str = ""
    YOUTUBE_OAUTH_TOKEN_PATH: str = "config/youtube_token.json"

    # -- Meta/Facebook ---------------------------------------------------------
    META_ACCESS_TOKEN: str = ""
    META_PAGE_ID: str = ""

    # -- Database --------------------------------------------------------------
    DATABASE_URL: str = "sqlite:///./jake_dms.db"
    POSTGRES_URL: str = "postgresql+asyncpg://jake:jake@localhost:5432/jake_dms"

    # -- Demo Mode -------------------------------------------------------------
    DEMO_MODE: bool = True
    DATA_DIR: Path = Path(__file__).resolve().parent.parent.parent / "data"

    # -- Logging ---------------------------------------------------------------
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    # -- Intacct ---------------------------------------------------------------
    INTACCT_SENDER_ID: str = ""
    INTACCT_SENDER_PASSWORD: str = ""
    INTACCT_COMPANY_ID: str = ""
    INTACCT_USER_ID: str = ""
    INTACCT_USER_PASSWORD: str = ""
    INTACCT_ENDPOINT: str = "https://api.intacct.com/ia/xml/xmlgw.phtml"
    INTACCT_MOCK_MODE: bool = True

    # -- Telegram --------------------------------------------------------------
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # -- LLM -------------------------------------------------------------------
    LLM_MODEL: str = "claude-sonnet-4-20250514"
    LLM_API_KEY: str = ""

    # -- Scheduler -------------------------------------------------------------
    SCHEDULER_TIMEZONE: str = "America/Los_Angeles"

    # -- FastAPI ---------------------------------------------------------------
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
