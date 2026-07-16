"""A compact read model suitable for a UI, API, or scheduled report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from analytics import queries


def dashboard_data(warehouse_path: str | Path | None = None) -> dict[str, list[dict[str, Any]]]:
    """Return all supported analytics panels from an existing warehouse snapshot."""
    return {
        "most_profitable_categories": queries.most_profitable_categories(warehouse_path),
        "average_flipscore": queries.average_flipscore(warehouse_path),
        "median_asking_prices": queries.median_asking_prices(warehouse_path),
        "price_reductions": queries.price_reductions(warehouse_path),
        "seller_frequency": queries.seller_frequency(warehouse_path),
        "keyword_performance": queries.keyword_performance(warehouse_path),
        "category_trends": queries.category_trends(warehouse_path),
        "daily_listing_volume": queries.daily_listing_volume(warehouse_path),
    }
