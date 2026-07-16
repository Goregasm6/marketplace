"""Marketplace-neutral listing parsing and product recognition helpers."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from categories import all_brands, keyword_catalog


# Compatibility exports backed by discovered category knowledge modules rather
# than a second, hardcoded category catalog.
DEFAULT_BRANDS: tuple[str, ...] = all_brands()
DEFAULT_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = keyword_catalog()


def normalize_title(value: str | None) -> str:
    """Produce stable, punctuation-free text suitable for matching."""
    # Replace punctuation before ASCII transliteration so Unicode separators
    # (for example an em dash) cannot silently join two words.
    source = re.sub(r"[^\w\s]", " ", value or "")
    text = unicodedata.normalize("NFKD", source).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


class ParsedListing(BaseModel):
    """A marketplace-independent representation used by the valuation pipeline."""

    model_config = ConfigDict(frozen=True)

    title: str
    description: str = ""
    asking_price: Optional[float] = Field(default=None, ge=0)
    normalized_title: str
    recognized_brand: Optional[str] = None
    recognized_model: Optional[str] = None
    category: Optional[str] = None
    matched_keywords: list[str] = Field(default_factory=list)


def _read_listing_field(listing: Mapping[str, Any] | Any, field: str, default: Any = None) -> Any:
    if isinstance(listing, Mapping):
        return listing.get(field, default)
    return getattr(listing, field, default)


def extract_brand(text: str, brands: Sequence[str] = DEFAULT_BRANDS) -> str | None:
    normalized = normalize_title(text)
    for brand in sorted(brands, key=lambda item: len(normalize_title(item)), reverse=True):
        pattern = rf"(?<!\w){re.escape(normalize_title(brand))}(?!\w)"
        if re.search(pattern, normalized):
            return brand
    return None


def extract_model(text: str, brand: str | None = None) -> str | None:
    """Extract common consumer-product model identifiers without source-specific rules."""
    original = " ".join((text or "").split())
    normalized = normalize_title(original)
    if brand and normalize_title(brand) == "apple":
        match = re.search(r"\b(iphone\s+(?:\d{1,2}(?:\s+(?:pro|max|mini|plus))?|se|xr|xs(?:\s+max)?))\b", normalized)
        if match:
            parts = match.group(1).split()
            return " ".join("iPhone" if word == "iphone" else word.capitalize() if not word.isdigit() else word for word in parts)
        match = re.search(r"\b(ipad(?:\s+(?:pro|air|mini))?(?:\s+\d+(?:st|nd|rd|th)\s+gen)?)\b", normalized)
        if match:
            return " ".join(word.capitalize() if word != "ipad" else "iPad" for word in match.group(1).split())

    # Identifiers such as WH-1000XM4, XPS-13, D850, and PS5 are stronger than
    # arbitrary title words and work across product categories.
    match = re.search(r"\b([A-Za-z]{1,8}(?:[- ]?\d)[A-Za-z0-9-]*)\b", original)
    return match.group(1) if match else None


def detect_category(
    text: str,
    category_keywords: Mapping[str, Sequence[str]] = DEFAULT_CATEGORY_KEYWORDS,
) -> tuple[str | None, list[str]]:
    normalized = normalize_title(text)
    padded = f" {normalized} "
    matches: list[tuple[str, list[str]]] = []
    for category, keywords in category_keywords.items():
        found = [
            keyword for keyword in keywords
            if f" {normalize_title(keyword)} " in padded
        ]
        if found:
            matches.append((category, found))
    if not matches:
        return None, []
    category, keywords = max(matches, key=lambda item: len(item[1]))
    return category, keywords


def parse_listing(
    listing: Mapping[str, Any] | Any,
    *,
    brands: Sequence[str] = DEFAULT_BRANDS,
    category_keywords: Mapping[str, Sequence[str]] = DEFAULT_CATEGORY_KEYWORDS,
) -> ParsedListing:
    """Parse a dict, Pydantic/SQLModel object, or other attribute-based listing."""
    title = str(_read_listing_field(listing, "title", "") or "").strip()
    if not title:
        raise ValueError("A listing title is required for valuation.")
    description = str(_read_listing_field(listing, "description", "") or "")
    price = _read_listing_field(listing, "price", _read_listing_field(listing, "asking_price"))
    brand = extract_brand(title, brands)
    category, keywords = detect_category(f"{title} {description}", category_keywords)
    return ParsedListing(
        title=title,
        description=description,
        asking_price=float(price) if price is not None else None,
        normalized_title=normalize_title(title),
        recognized_brand=brand,
        recognized_model=extract_model(title, brand),
        category=category,
        matched_keywords=keywords,
    )
