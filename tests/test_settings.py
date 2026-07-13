from pathlib import Path

import pytest
from pydantic import ValidationError

from config.settings import Settings


def test_settings_loads_values_from_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "SQLITE_PATH=/tmp/maie.db",
                "SEARCH_INTERVAL=7",
                "SEARCH_RADIUS=12",
                "DISCORD_WEBHOOK=https://discord.com/api/webhooks/123/abc",
                "TELEGRAM_TOKEN=123456789:ABCDEF1234567890",
                "MINIMUM_FLIPSCORE=80",
                "MINIMUM_EXPECTED_PROFIT=45.5",
                "LOGGING_LEVEL=DEBUG",
                "ENABLED_COLLECTORS=craigslist,ebay",
                "ENABLED_CATEGORIES=electronics,tools",
            ]
        )
    )

    settings = Settings(_env_file=env_file)

    assert settings.sqlite_path == Path("/tmp/maie.db")
    assert settings.search_interval == 7
    assert settings.search_radius == 12
    assert settings.discord_webhook == "https://discord.com/api/webhooks/123/abc"
    assert settings.telegram_token == "123456789:ABCDEF1234567890"
    assert settings.minimum_flipscore == 80
    assert settings.minimum_expected_profit == 45.5
    assert settings.logging_level == "DEBUG"
    assert settings.enabled_collectors == ["craigslist", "ebay"]
    assert settings.enabled_categories == ["electronics", "tools"]


def test_settings_rejects_invalid_values() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(discord_webhook="https://example.com/not-a-webhook")

    message = str(exc_info.value)
    assert "Discord webhook" in message
    assert "valid Discord webhook URL" in message

    with pytest.raises(ValidationError) as exc_info:
        Settings(logging_level="VERBOSE")

    message = str(exc_info.value)
    assert "logging_level" in message
    assert "DEBUG, INFO, WARNING, ERROR, CRITICAL" in message
