from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ListingContext:
    """Minimal listing payload passed between existing collectors and future AI modules."""

    title: str | None = None
    description: str | None = None
    price: float | None = None
    category: str | None = None
    url: str | None = None
    source: str | None = None
    external_id: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisArtifacts:
    """Optional enrichment data produced by analysis plugins."""

    ocr_text: str | None = None
    image_labels: list[str] = field(default_factory=list)
    detected_objects: list[str] = field(default_factory=list)
    embeddings: list[float] | None = None
    llm_summary: str | None = None
    price_prediction: float | None = None
    duplicate_score: float | None = None
    recommendation: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


class AIPlugin(Protocol):
    """Small interface for future AI integrations."""

    name: str

    def run(
        self, context: ListingContext, artifacts: AnalysisArtifacts
    ) -> AnalysisArtifacts:
        """Return updated artifacts after processing a listing."""


class PluginRegistry:
    """Very small registry for optional analysis plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, AIPlugin] = {}

    def register(self, plugin: AIPlugin) -> None:
        self._plugins[plugin.name.lower()] = plugin

    def get(self, name: str) -> AIPlugin | None:
        return self._plugins.get(name.lower())

    def all(self) -> list[AIPlugin]:
        return list(self._plugins.values())


def run_plugins(
    context: ListingContext,
    plugins: list[AIPlugin] | None = None,
    artifacts: AnalysisArtifacts | None = None,
) -> AnalysisArtifacts:
    """Apply a sequence of plugins to a listing context without changing the core flow."""

    result = artifacts or AnalysisArtifacts()
    for plugin in plugins or []:
        result = plugin.run(context, result)
    return result
