from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


def _parse_csv_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item.strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if not value.strip():
            return []
        return [item.strip() for item in value.split(",") if item.strip()]
    raise TypeError("Expected a comma-separated string or a list of values")


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env files."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="maie", description="Application name shown in CLI output and logs.")
    environment: str = Field(default="development", description="Deployment environment name.")
    debug: bool = Field(default=False, description="Enable verbose debug diagnostics.")
    sqlite_path: Path = Field(
        default=BASE_DIR / "database" / "listings.db",
        description="Path to the SQLite database file used by the application.",
    )
    search_interval: int = Field(default=15, ge=1, description="How often searches should run, in minutes.")
    search_radius: int = Field(default=25, ge=1, description="Maximum search radius in miles.")
    discord_webhook: Optional[str] = Field(default=None, description="Discord webhook URL for sending alerts.")
    telegram_token: Optional[str] = Field(default=None, description="Telegram bot token for sending alerts.")
    minimum_flipscore: int = Field(
        default=60,
        ge=0,
        le=100,
        description="Minimum FlipScore required for an opportunity to be surfaced.",
    )
    minimum_expected_profit: float = Field(
        default=20.0,
        ge=0.0,
        description="Minimum expected profit in dollars required for a listing to be considered.",
    )
    logging_level: str = Field(
        default="INFO",
        description="Logging verbosity. Supported values: DEBUG, INFO, WARNING, ERROR, CRITICAL.",
    )
    enabled_collectors: Any = Field(
        default_factory=lambda: ["craigslist"],
        description="Comma-separated collector names that should be enabled.",
    )
    enabled_categories: Any = Field(
        default_factory=lambda: ["electronics", "tools"],
        description="Comma-separated category slugs that should be enabled.",
    )

    @field_validator("sqlite_path", mode="before")
    @classmethod
    def _normalize_sqlite_path(cls, value: Any) -> Path:
        if value in (None, ""):
            return BASE_DIR / "database" / "listings.db"
        if isinstance(value, Path):
            path = value
        elif isinstance(value, str):
            path = Path(value.strip())
        else:
            raise TypeError("sqlite_path must be a path-like value")

        if not path.is_absolute():
            path = (BASE_DIR / path).resolve()
        return path

    @field_validator("enabled_collectors", "enabled_categories", mode="before")
    @classmethod
    def _parse_enabled_options(cls, value: Any) -> List[str]:
        return _parse_csv_list(value)

    @field_validator("discord_webhook", mode="before")
    @classmethod
    def _validate_discord_webhook(cls, value: Any) -> Optional[str]:
        if value in (None, ""):
            return None
        if not isinstance(value, str):
            raise TypeError("Discord webhook must be provided as a string")

        normalized = value.strip()
        if "discord.com" not in normalized and "discordapp.com" not in normalized:
            raise ValueError(
                "Discord webhook must be a valid Discord webhook URL, for example https://discord.com/api/webhooks/..."
            )
        if "/api/webhooks/" not in normalized:
            raise ValueError(
                "Discord webhook must point to a Discord webhook endpoint, for example https://discord.com/api/webhooks/..."
            )
        return normalized

    @field_validator("telegram_token", mode="before")
    @classmethod
    def _validate_telegram_token(cls, value: Any) -> Optional[str]:
        if value in (None, ""):
            return None
        if not isinstance(value, str):
            raise TypeError("Telegram token must be provided as a string")

        normalized = value.strip()
        if ":" not in normalized:
            raise ValueError("Telegram token must look like 123456789:ABCDEF1234567890")
        return normalized

    @field_validator("logging_level")
    @classmethod
    def _validate_logging_level(cls, value: str) -> str:
        normalized = value.strip().upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if normalized not in allowed:
            raise ValueError("logging_level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        return normalized


settings = Settings()
