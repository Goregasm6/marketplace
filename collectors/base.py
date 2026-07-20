"""Generic collector framework for marketplace integrations."""

from __future__ import annotations

import importlib
import pkgutil
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Iterable

from uuid import uuid4
from core.plugins import CollectorPlugin
from core.events.bus import bus
from core.events.base import (
    ListingDiscovered,
    CollectorStarted,
    CollectorFinished,
    CollectorFailed
)

from analysis.search import SearchGenerator


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


class BaseCollector(CollectorPlugin, ABC):
    """Abstract base class for all marketplace collectors."""

    name: str | None = None

    def generate_search_queries(
        self, query: str, *, category: str | None = None, max_queries: int = 24
    ) -> list[str]:
        """Expand a seed query into optimized collector searches."""
        category_plugin = self._resolve_category(category)
        generator = SearchGenerator(category=category_plugin)
        return generator.generate(query, max_queries=max_queries)

    def _resolve_category(self, category: str | None) -> Any | None:
        if not category:
            return None
        from categories.catalog import get_category

        return get_category(category)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls is BaseCollector:
            return
        collector_name = getattr(cls, "name", None) or cls.__name__
        CollectorRegistry.register(collector_name, cls)
        CollectorRegistry.register(cls.__name__, cls)

    @abstractmethod
    async def search(self, query: str, **kwargs: Any) -> Any:
        """Fetch the raw search results from a marketplace."""

    @abstractmethod
    async def fetch(self, search_results: Any, **kwargs: Any) -> Any:
        """Retrieve the relevant listing payloads from search results."""

    @abstractmethod
    async def normalize(self, item: Any, **kwargs: Any) -> Any:
        """Normalize a fetched item into a consistent internal representation."""

    @abstractmethod
    async def validate(self, item: Any, **kwargs: Any) -> bool:
        """Return True when a normalized item is acceptable to persist."""

    @abstractmethod
    async def save(self, items: Iterable[Any], **kwargs: Any) -> Any:
        """Persist the validated items through the configured storage layer."""

    async def run(self, query: str, **kwargs: Any) -> Any:
        """Execute the full pipeline for a search query."""
        session_id = uuid4()
        collector_name = getattr(self, "name", None) or self.__class__.__name__
        
        await bus.publish(CollectorStarted(
            collector_name=collector_name,
            session_id=session_id
        ))

        try:
            search_queries = kwargs.get("search_queries")
            if search_queries is None and kwargs.get("expand_searches", False):
                search_queries = self.generate_search_queries(
                    query, category=kwargs.get("category")
                )

            if search_queries is None:
                search_queries = [query]
            elif isinstance(search_queries, str):
                search_queries = [search_queries]
            elif not isinstance(search_queries, (list, tuple, set)):
                search_queries = [search_queries]

            listings_count = 0
            for search_query in search_queries:
                search_results = await self.search(search_query, **kwargs)
                fetched_items = await self.fetch(search_results, **kwargs)

                if fetched_items is None:
                    fetched_items = []
                elif isinstance(fetched_items, (str, bytes)):
                    fetched_items = [fetched_items]
                elif not isinstance(fetched_items, (list, tuple, set)):
                    fetched_items = [fetched_items]

                for item in fetched_items:
                    normalized_item = await self.normalize(item, **kwargs)
                    
                    # Instead of validating and saving directly, we publish an event
                    # Validation and persistence are now decoupled subscribers
                    await bus.publish(ListingDiscovered(
                        external_id=normalized_item.get("external_id", "unknown"),
                        source=normalized_item.get("source", self.name or "unknown"),
                        data=normalized_item
                    ))
                    listings_count += 1

            await bus.publish(CollectorFinished(
                collector_name=collector_name,
                session_id=session_id,
                listings_count=listings_count
            ))
            return listings_count

        except Exception as e:
            import traceback
            await bus.publish(CollectorFailed(
                collector_name=collector_name,
                session_id=session_id,
                error=str(e),
                stack_trace=traceback.format_exc()
            ))
            raise e


def discover_collectors(package_name: str = "collectors") -> list[type[BaseCollector]]:
    """Import collector modules and return all registered collector classes."""
    package = importlib.import_module(package_name)
    for _, module_name, _ in pkgutil.iter_modules(
        package.__path__, package.__name__ + "."
    ):
        if module_name.endswith(".base"):
            continue
        importlib.import_module(module_name)
    return CollectorRegistry.all()


__all__ = ["BaseCollector", "CollectorRegistry", "discover_collectors"]
