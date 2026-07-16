from __future__ import annotations

import sys
from pathlib import Path

from core.plugins import (
    AnalyzerPlugin,
    BasePlugin,
    CategoryPlugin,
    CollectorPlugin,
    NotificationPlugin,
    PluginLoader,
    PluginRegistry,
)


def clear_registry(registry: PluginRegistry) -> None:
    registry._plugins.clear()


def test_base_plugin_registers_with_registry_by_type():
    registry = PluginRegistry()
    clear_registry(registry)

    class SampleCollector(CollectorPlugin):
        name = "sample-collector"
        version = "1.0.0"
        author = "Test"
        description = "Test collector"
        dependencies = ["requests"]
        capabilities = ["search"]

    plugin = SampleCollector(registry=registry)

    assert registry.get("sample-collector") is plugin
    assert registry.get_collectors() == [plugin]
    assert registry.get_categories() == []
    assert registry.get_notifications() == []


def test_registry_filters_by_plugin_type():
    registry = PluginRegistry()
    clear_registry(registry)

    class SampleCategory(CategoryPlugin):
        name = "sample-category"
        version = "1.0.0"
        author = "Test"
        description = "Test category"
        dependencies = []
        capabilities = ["classification"]

    class SampleAnalyzer(AnalyzerPlugin):
        name = "sample-analyzer"
        version = "1.0.0"
        author = "Test"
        description = "Test analyzer"
        dependencies = []
        capabilities = ["scoring"]

    class SampleNotification(NotificationPlugin):
        name = "sample-notification"
        version = "1.0.0"
        author = "Test"
        description = "Test notification"
        dependencies = []
        capabilities = ["email"]

    SampleCategory(registry=registry)
    SampleAnalyzer(registry=registry)
    SampleNotification(registry=registry)

    assert registry.get_categories()[0].name == "sample-category"
    assert registry.get_analyzers()[0].name == "sample-analyzer"
    assert registry.get_notifications()[0].name == "sample-notification"


def test_loader_discovers_plugins_from_modules(tmp_path, monkeypatch):
    registry = PluginRegistry()
    clear_registry(registry)

    package_dir = tmp_path / "sample_plugins"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "demo.py").write_text(
        "from core.plugins import CollectorPlugin\n"
        "class DemoCollector(CollectorPlugin):\n"
        "    name = 'demo-collector'\n"
        "    version = '0.1.0'\n"
        "    author = 'Test'\n"
        "    description = 'Demo collector'\n"
        "    dependencies = []\n"
        "    capabilities = ['demo']\n",
        encoding="utf-8",
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    loader = PluginLoader(registry=registry)
    discovered = loader.discover(packages=["sample_plugins"])

    assert any(plugin.name == "demo-collector" for plugin in discovered)
    assert registry.get_collectors()[0].name == "demo-collector"


def test_plugin_metadata_is_exposed_on_instances():
    class SamplePlugin(BasePlugin):
        name = "sample-plugin"
        version = "2.0.0"
        author = "Test"
        description = "Sample plugin"
        dependencies = ["numpy"]
        capabilities = ["demo"]
        plugin_type = "future-ai"

    plugin = SamplePlugin(registry=PluginRegistry())

    assert plugin.metadata["name"] == "sample-plugin"
    assert plugin.metadata["version"] == "2.0.0"
    assert plugin.metadata["dependencies"] == ["numpy"]
    assert plugin.metadata["capabilities"] == ["demo"]
