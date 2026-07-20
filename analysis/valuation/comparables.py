"""Provider contracts and data structures for comparable-product prices."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Optional, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from .parser import ParsedListing


class ComparableProduct(BaseModel):
    """A product price observation returned by a pricing provider."""

    model_config = ConfigDict(frozen=True)

    title: str
    price: float = Field(ge=0)
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    condition: Optional[str] = None
    sold_at: Optional[datetime] = None
    source: Optional[str] = None


@runtime_checkable
class PricingProvider(Protocol):
    """Implement this protocol to add any future pricing data source."""

    name: str

    def find_comparables(
        self, listing: ParsedListing
    ) -> Sequence[ComparableProduct]: ...


class InMemoryPricingProvider:
    """Simple provider useful for tests, fixtures, and local catalog imports."""

    name = "in_memory"

    def __init__(self, products: Iterable[ComparableProduct]) -> None:
        self._products = tuple(products)

    def find_comparables(self, listing: ParsedListing) -> Sequence[ComparableProduct]:
        return self._products
