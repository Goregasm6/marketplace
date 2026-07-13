from pathlib import Path

from config.settings import settings


BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE = str(settings.sqlite_path)
SEARCH_INTERVAL = settings.search_interval
SEARCH_RADIUS = settings.search_radius
DISCORD_WEBHOOK = settings.discord_webhook
TELEGRAM_TOKEN = settings.telegram_token
MINIMUM_FLIPSCORE = settings.minimum_flipscore
MINIMUM_EXPECTED_PROFIT = settings.minimum_expected_profit
LOGGING_LEVEL = settings.logging_level
ENABLED_COLLECTORS = settings.enabled_collectors
ENABLED_CATEGORIES = settings.enabled_categories