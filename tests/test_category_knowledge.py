from categories import get_categories, get_category
from core.plugins import PluginLoader, PluginRegistry


def test_builtin_category_modules_expose_complete_knowledge() -> None:
    categories = get_categories()

    assert len(categories) >= 10
    for category in categories:
        assert category.brands
        assert category.keywords
        assert category.common_misspellings
        assert category.seasonality
        assert category.repair_opportunities
        assert category.shipping_profile.method
        assert category.typical_margins.high >= category.typical_margins.low > 0
        assert category.pricing_providers
        assert category.common_model_prefixes
        assert category.related_categories


def test_category_modules_are_plugin_discoverable() -> None:
    registry = PluginRegistry()
    PluginLoader(registry=registry).discover(packages=["categories"])

    assert len(registry.get_categories()) >= 10
    assert get_category("power_tools").category == "power-tools"
