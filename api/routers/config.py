from typing import Any

from fastapi import APIRouter
from config.settings import settings

router = APIRouter(prefix="/config", tags=["configuration"])


@router.get("/", response_model=dict)
def get_config() -> Any:
    """Retrieve the current application configuration."""
    return settings.model_dump(
        exclude={
            "api_key",
            "secret_key",
            "ai_api_key",
            "telegram_token",
            "discord_webhook",
        }
    )
