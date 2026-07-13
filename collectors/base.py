"""Generic collector framework for marketplace integrations."""

from __future__ import annotations

import importlib
import pkgutil
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Iterable


class CollectorRegistry:
    """Registry for discoverable collector subclasses."""

    _registry: ClassVar[dict[str, type["BaseCollector"]]] = {}

    @classmethod
    def register(cls, name: str, collector_cls: type["BaseCollector"]) -> None:
        cls._registry[name.lower()] = collector_cls

    @classmethod
    def get(cls, name: str) -> type["BaseCollector"] | None:
        if not name:
            return None
        return cls._registry.get(name.lower())

    @classmethod
    def all(cls) -> list[type["BaseCollector"]]:
        return list(cls._registry.values())


class BaseCollector(ABC):
    """Abstract base class for all marketplace collectors."""

    name: str | None = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls is BaseCollector:
            return
        collector_name = getattr(cls, "name", None) or cls.__name__
        CollectorRegistry.register(collector_name, cls)
        CollectorRegistry.register(cls.__name__, cls)

    @abstractmethod
    def search(self, query: str, **kwargs: Any) -> Any:
        """Fetch the raw search results from a marketplace."""

    @abstractmethod
    def fetch(self, search_results: Any, **kwargs: Any) -> Any:
        """Retrieve the relevant listing payloads from search results."""

    @abstractmethod
    def normalize(self, item: Any, **kwargs: Any) -> Any:
        """Normalize a fetched item into a consistent internal representation."""

    @abstractmethod
    def validate(self, item: Any, **kwargs: Any) -> bool:
        """Return True when a normalized item is acceptable to persist."""

    @abstractmethod
    def save(self, items: Iterable[Any], **kwargs: Any) -> Any:
        """Persist the validated items through the configured storage layer."""

    def run(self, query: str, **kwargs: Any) -> Any:
        """Execute the full pipeline for a search query."""
        search_results = self.search(query, **kwargs)
        fetched_items = self.fetch(search_results, **kwargs)

        if fetched_items is None:
            fetched_items = []
        elif isinstance(fetched_items, (str, bytes)):
            fetched_items = [fetched_items]
        elif not isinstance(fetched_items, (list, tuple, set)):
            fetched_items = [fetched_items]

        normalized_items = []
        for item in fetched_items:
            normalized_item = self.normalize(item, **kwargs)
            if self.validate(normalized_item, **kwargs):
                normalized_items.append(normalized_item)

        return self.save(normalized_items, **kwargs)


def discover_collectors(package_name: str = "collectors") -> list[type[BaseCollector]]:
    """Import collector modules and return all registered collector classes."""
    package = importlib.import_module(package_name)
    for _, module_name, _ in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        if module_name.endswith(".base"):
            continue
        importlib.import_module(module_name)
    return CollectorRegistry.all()


__all__ = ["BaseCollector", "CollectorRegistry", "discover_collectors"]
