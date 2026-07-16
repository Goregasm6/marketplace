"""Composable valuation orchestration and result model."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from statistics import median
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from .comparables import ComparableProduct, PricingProvider
from .confidence import calculate_confidence
from .matcher import ComparableMatch, find_matches
from .parser import DEFAULT_BRANDS, DEFAULT_CATEGORY_KEYWORDS, ParsedListing, parse_listing


class ValuationResult(BaseModel):
    """The provider-neutral output returned by :class:`ValuationEngine`."""

    model_config = ConfigDict(frozen=True)

    estimated_market_value: Optional[float] = Field(default=None, ge=0)
    estimated_resale_value: Optional[float] = Field(default=None, ge=0)
    confidence: float = Field(ge=0, le=1)
    recognized_brand: Optional[str] = None
    recognized_model: Optional[str] = None
    matched_keywords: list[str] = Field(default_factory=list)
    reasoning: list[str] = Field(default_factory=list)


class ValuationEngine:
    """Coordinates parsing, matching, estimation, and confidence calculation."""

    def __init__(
        self,
        providers: Sequence[PricingProvider] = (),
        *,
        resale_rate: float = 0.85,
        minimum_match_score: float = 0.35,
        brands: Sequence[str] = DEFAULT_BRANDS,
        category_keywords: Mapping[str, Sequence[str]] = DEFAULT_CATEGORY_KEYWORDS,
    ) -> None:
        if not 0 < resale_rate <= 1:
            raise ValueError("resale_rate must be greater than 0 and no greater than 1.")
        self.providers = tuple(providers)
        self.resale_rate = resale_rate
        self.minimum_match_score = minimum_match_score
        self.brands = tuple(brands)
        self.category_keywords = category_keywords

    def value(self, listing: Mapping[str, Any] | Any) -> ValuationResult:
        parsed = parse_listing(listing, brands=self.brands, category_keywords=self.category_keywords)
        matches = self._find_comparables(parsed)
        prices = [match.comparable.price for match in matches]
        keywords = sorted({keyword for match in matches for keyword in match.matched_keywords} | set(parsed.matched_keywords))
        reasoning = self._reasoning(parsed, matches)
        if not prices:
            return ValuationResult(
                confidence=0.0,
                recognized_brand=parsed.recognized_brand,
                recognized_model=parsed.recognized_model,
                matched_keywords=keywords,
                reasoning=reasoning,
            )
        market_value = round(float(median(prices)), 2)
        confidence = calculate_confidence(
            match_scores=[match.score for match in matches], prices=prices,
            recognized=bool(parsed.recognized_brand or parsed.recognized_model),
        )
        reasoning.insert(0, f"Estimated market value from {len(prices)} matched comparable(s) using the median sale price.")
        return ValuationResult(
            estimated_market_value=market_value,
            estimated_resale_value=round(market_value * self.resale_rate, 2),
            confidence=confidence,
            recognized_brand=parsed.recognized_brand,
            recognized_model=parsed.recognized_model,
            matched_keywords=keywords,
            reasoning=reasoning,
        )

    def _find_comparables(self, parsed: ParsedListing) -> list[ComparableMatch]:
        products: list[ComparableProduct] = []
        for provider in self.providers:
            products.extend(provider.find_comparables(parsed))
        return find_matches(parsed, products, minimum_score=self.minimum_match_score)

    @staticmethod
    def _reasoning(parsed: ParsedListing, matches: Sequence[ComparableMatch]) -> list[str]:
        reasons = []
        if parsed.recognized_brand:
            reasons.append(f"Recognized brand: {parsed.recognized_brand}.")
        if parsed.recognized_model:
            reasons.append(f"Recognized model: {parsed.recognized_model}.")
        if parsed.category:
            reasons.append(f"Detected category: {parsed.category}.")
        if not matches:
            reasons.append("No sufficiently similar comparable products were found.")
        return reasons


def estimate_value(listing: Mapping[str, Any] | Any, providers: Sequence[PricingProvider] = ()) -> ValuationResult:
    """Convenience entry point for callers that do not need a long-lived engine."""
    return ValuationEngine(providers).value(listing)
