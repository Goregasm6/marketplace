from __future__ import annotations

import abc
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BaseParser(Protocol):
    """Protocol defining the interface for marketplace parsers."""

    @abc.abstractmethod
    def parse(self, html: str) -> list[dict[str, Any]]:
        """Parse HTML content into a list of listing dictionaries."""
        ...


class ParserRegistry:
    """Registry to manage and retrieve parser instances."""

    _parsers: dict[str, type[BaseParser]] = {}

    @classmethod
    def register(cls, name: str, parser_cls: type[BaseParser]) -> None:
        """Register a parser class with a name."""
        cls._parsers[name] = parser_cls

    @classmethod
    def get(cls, name: str) -> BaseParser:
        """Get an instance of a registered parser by name."""
        parser_cls = cls._parsers.get(name)
        if not parser_cls:
            raise ValueError(f"No parser registered for: {name}")
        return parser_cls()
