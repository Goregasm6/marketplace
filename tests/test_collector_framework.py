import pytest

from collectors.base import BaseCollector, CollectorRegistry, discover_collectors


class DummyCollector(BaseCollector):
    name = "dummy"

    def search(self, query, **kwargs):
        return [{"query": query}]

    def fetch(self, search_results, **kwargs):
        return search_results

    def normalize(self, item, **kwargs):
        return {"query": item["query"], "normalized": True}

    def validate(self, item, **kwargs):
        return bool(item.get("query"))

    def save(self, items, **kwargs):
        return len(items)


def test_base_collector_registers_concrete_subclasses():
    assert CollectorRegistry.get("DummyCollector") is DummyCollector
    assert CollectorRegistry.get("dummy") is DummyCollector


def test_base_collector_cannot_be_instantiated_without_implementations():
    with pytest.raises(TypeError):

        class BrokenCollector(BaseCollector):
            pass

        BrokenCollector()


def test_run_orchestrates_the_collector_pipeline():
    collector = DummyCollector()
    assert collector.run("books") == 1


def test_discover_collectors_imports_modules_from_the_package():
    collectors = discover_collectors()
    assert DummyCollector in collectors
