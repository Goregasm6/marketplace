"""Discovery and lookup helpers for category knowledge plugins."""

from __future__ import annotations

from functools import lru_cache

from core.plugins import PluginLoader, PluginRegistry

from .base import CategoryKnowledge


@lru_cache(maxsize=1)
def get_categories() -> tuple[CategoryKnowledge, ...]:
    """Load built-in category modules once, in deterministic slug order."""
    registry = PluginRegistry()
    PluginLoader(registry=registry).discover(packages=["categories"])
    plugins = [
        plugin
        for plugin in registry.get_categories()
        if isinstance(plugin, CategoryKnowledge)
    ]
    return tuple(sorted(plugins, key=lambda plugin: plugin.category))


@lru_cache(maxsize=1)
def _category_map() -> dict[str, CategoryKnowledge]:
    return {plugin.category: plugin for plugin in get_categories()}


def get_category(slug: str | None) -> CategoryKnowledge | None:
    normalized = (slug or "").strip().lower().replace("_", "-")
    return _category_map().get(normalized)


def all_brands() -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            brand for category in get_categories() for brand in category.brands
        )
    )


def keyword_catalog() -> dict[str, tuple[str, ...]]:
    """Compatibility view for callers that accept category-to-keyword mappings."""
    return {
        category.category: tuple(
            dict.fromkeys(
                (
                    *category.keywords,
                    *category.brands,
                    *category.common_misspellings,
                    *category.common_model_prefixes,
                )
            )
        )
        for category in get_categories()
    }
