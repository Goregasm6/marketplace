"""Comparable-product matching independent of any pricing provider."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .parser import ParsedListing, normalize_title


@dataclass(frozen=True)
class ComparableMatch:
    comparable: object
    score: float
    matched_keywords: tuple[str, ...]


def _tokens(value: str) -> set[str]:
    return set(normalize_title(value).split())


def match_score(listing: ParsedListing, comparable: object) -> tuple[float, tuple[str, ...]]:
    title = str(getattr(comparable, "title", ""))
    comparable_tokens = _tokens(title)
    listing_tokens = _tokens(listing.normalized_title)
    shared = tuple(sorted(listing_tokens & comparable_tokens))
    union = listing_tokens | comparable_tokens
    score = len(shared) / len(union) if union else 0.0
    if listing.recognized_brand and normalize_title(str(getattr(comparable, "brand", "") or "")) == normalize_title(listing.recognized_brand):
        score += 0.25
    if listing.recognized_model and normalize_title(listing.recognized_model) in normalize_title(title):
        score += 0.35
    if listing.category and getattr(comparable, "category", None) == listing.category:
        score += 0.10
    return min(score, 1.0), shared


def find_matches(
    listing: ParsedListing, comparables: Iterable[object], *, minimum_score: float = 0.35
) -> list[ComparableMatch]:
    matches = []
    for comparable in comparables:
        score, keywords = match_score(listing, comparable)
        if score >= minimum_score:
            matches.append(ComparableMatch(comparable, score, keywords))
    return sorted(matches, key=lambda match: match.score, reverse=True)
