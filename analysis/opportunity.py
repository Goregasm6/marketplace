from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional
import re
from core.ai.tasks import AIService
from config.settings import settings


@dataclass(frozen=True)
class OpportunityFactor:
    """A specific reason why a listing is considered an opportunity."""

    name: str
    score_impact: (
        float  # 0 to 100, how much this factor contributes to the overall score
    )
    reason: str
    category: str  # e.g., "Metadata", "Listing Quality", "Seller", "Market"


@dataclass
class OpportunityResult:
    """The result of an opportunity analysis."""

    opportunity_score: float  # 0 to 100
    factors: List[OpportunityFactor] = field(default_factory=list)

    @property
    def explanation(self) -> str:
        if not self.factors:
            return "No hidden opportunities detected."
        return " ".join([f.reason for f in self.factors])


class OpportunityDetector:
    """Base class for opportunity detection plugins."""

    name: str = "base_detector"
    description: str = "Base opportunity detector"

    def detect(self, listing: dict[str, Any]) -> List[OpportunityFactor]:
        """Detect opportunities in a listing."""
        raise NotImplementedError


class OpportunityEngine:
    """Engine that runs multiple detectors to identify hidden opportunities."""

    def __init__(self, detectors: Optional[List[OpportunityDetector]] = None):
        self.detectors = detectors or []

    def add_detector(self, detector: OpportunityDetector):
        self.detectors.append(detector)

    def analyze(self, listing: dict[str, Any]) -> OpportunityResult:
        all_factors = []
        for detector in self.detectors:
            factors = detector.detect(listing)
            all_factors.extend(factors)

        # Calculate a weighted score. For now, we'll use a simple sum capped at 100.
        # Different factors might have different weights in a more complex engine.
        total_score = sum(f.score_impact for f in all_factors)
        opportunity_score = min(100.0, total_score)

        return OpportunityResult(
            opportunity_score=opportunity_score, factors=all_factors
        )


# Concrete Detectors


class ListingQualityDetector(OpportunityDetector):
    """Detects opportunities based on poor listing quality (photos, titles, descriptions)."""

    name = "listing_quality"
    description = "Detects poor photos, generic titles, and incomplete descriptions."

    def detect(self, listing: dict[str, Any]) -> List[OpportunityFactor]:
        factors = []

        # Poor Photos (if we have image analysis data)
        image_quality = listing.get("image_quality_score")
        if image_quality is not None and image_quality < 40:
            factors.append(
                OpportunityFactor(
                    name="poor_photos",
                    score_impact=15,
                    reason="Low quality or few photos may deter other buyers.",
                    category="Listing Quality",
                )
            )
        elif not listing.get("images") or len(listing.get("images", [])) <= 1:
            factors.append(
                OpportunityFactor(
                    name="few_photos",
                    score_impact=10,
                    reason="Very few photos often hide the true value of an item.",
                    category="Listing Quality",
                )
            )

        # Generic Titles
        title = listing.get("title", "").lower()
        generic_terms = ["stuff", "items", "box", "collection", "junk", "clearance"]
        if any(term in title for term in generic_terms) or len(title) < 15:
            factors.append(
                OpportunityFactor(
                    name="generic_title",
                    score_impact=20,
                    reason="Generic or short title makes the listing harder to find for others.",
                    category="Listing Quality",
                )
            )

        # Incomplete Descriptions
        description = listing.get("description", "")
        if len(description) < 50:
            factors.append(
                OpportunityFactor(
                    name="incomplete_description",
                    score_impact=15,
                    reason="Minimal description often leads to lower competition.",
                    category="Listing Quality",
                )
            )

        return factors


class MetadataDetector(OpportunityDetector):
    """Detects missing or incorrect metadata (misspellings, wrong category, missing model numbers)."""

    name = "metadata"
    description = "Detects misspellings, wrong categories, and missing model numbers."

    def detect(self, listing: dict[str, Any]) -> List[OpportunityFactor]:
        factors = []

        # Missing Model Numbers
        title = listing.get("title", "")
        description = listing.get("description", "")
        # Simple regex for model numbers (letters followed by numbers or vice versa)
        model_pattern = r"\b[A-Z0-9]{3,}\b"
        has_model = re.search(model_pattern, title) or re.search(
            model_pattern, description
        )

        if not has_model:
            factors.append(
                OpportunityFactor(
                    name="missing_model_number",
                    score_impact=15,
                    reason="Missing model numbers make the listing less searchable for pros.",
                    category="Metadata",
                )
            )

        # Wrong Category (requires context from the collector/user)
        if listing.get("category_mismatch"):
            factors.append(
                OpportunityFactor(
                    name="wrong_category",
                    score_impact=25,
                    reason="Listing is in the wrong category, hiding it from targeted searches.",
                    category="Metadata",
                )
            )

        # Misspellings (Placeholder - would ideally use a spellchecker or AI)
        if listing.get("has_misspellings"):
            factors.append(
                OpportunityFactor(
                    name="misspellings",
                    score_impact=20,
                    reason="Typos in the title prevent the listing from appearing in common searches.",
                    category="Metadata",
                )
            )

        return factors


class MarketSignalsDetector(OpportunityDetector):
    """Detects market-based opportunities (bundle listings, seasonality, historical drops)."""

    name = "market_signals"
    description = "Detects bundles, seasonality, and historical price drops."

    def detect(self, listing: dict[str, Any]) -> List[OpportunityFactor]:
        factors = []

        # Bundle Listings
        title = listing.get("title", "").lower()
        bundle_terms = ["bundle", "lot", "collection", "set", "everything"]
        if any(term in title for term in bundle_terms):
            factors.append(
                OpportunityFactor(
                    name="bundle_listing",
                    score_impact=30,
                    reason="Bundle listings often provide lower per-item cost and higher flip potential.",
                    category="Market",
                )
            )

        # Historical Price Drops
        if listing.get("price_dropped_recently"):
            factors.append(
                OpportunityFactor(
                    name="historical_price_drop",
                    score_impact=20,
                    reason="Recent price drops indicate a seller eager to move the item.",
                    category="Market",
                )
            )

        # Seasonality (Placeholder - should check current date vs item type)
        if listing.get("off_season"):
            factors.append(
                OpportunityFactor(
                    name="off_season_listing",
                    score_impact=15,
                    reason="Buying off-season can lead to significant discounts.",
                    category="Market",
                )
            )

        return factors


class SpecializationDetector(OpportunityDetector):
    """Detects specialized opportunities (rare brands, industrial surplus, commercial equipment)."""

    name = "specialization"
    description = "Detects rare brands, industrial surplus, and commercial equipment."

    def detect(self, listing: dict[str, Any]) -> List[OpportunityFactor]:
        factors = []

        # Rare Brands
        if listing.get("rare_brand"):
            factors.append(
                OpportunityFactor(
                    name="rare_brand",
                    score_impact=25,
                    reason="Rare or niche brands often have high value but low general awareness.",
                    category="Specialization",
                )
            )

        # Industrial/Commercial
        category = listing.get("category", "").lower()
        if any(
            term in category for term in ["industrial", "commercial", "lab", "medical"]
        ):
            factors.append(
                OpportunityFactor(
                    name="commercial_equipment",
                    score_impact=20,
                    reason="Industrial and commercial equipment often has high resale value to specific buyers.",
                    category="Specialization",
                )
            )

        return factors


class SellerMotivationDetector(OpportunityDetector):
    """Detects seller-specific opportunities (motivation, repair needs)."""

    name = "seller_motivation"
    description = "Detects seller motivation and repair opportunities."

    def detect(self, listing: dict[str, Any]) -> List[OpportunityFactor]:
        factors = []

        # Motivation (moving, urgent, etc.)
        description = listing.get("description", "").lower()
        motivation_terms = ["moving", "must sell", "urgent", "leaving", "need cash"]
        if any(term in description for term in motivation_terms):
            factors.append(
                OpportunityFactor(
                    name="high_seller_motivation",
                    score_impact=25,
                    reason="Seller's urgency increases negotiation leverage.",
                    category="Seller",
                )
            )

        # Repair Opportunities
        repair_terms = ["needs repair", "not working", "for parts", "cracked", "broken"]
        if any(term in description for term in repair_terms):
            factors.append(
                OpportunityFactor(
                    name="repair_opportunity",
                    score_impact=20,
                    reason="Items needing minor repairs can be acquired at steep discounts.",
                    category="Seller",
                )
            )

        return factors


class AIDetector(OpportunityDetector):
    """Uses AI to detect subtle opportunities like misspellings and wrong categories."""

    name = "ai_detector"
    description = "Uses LLM to find hidden opportunities."

    def __init__(self, service: Optional[AIService] = None):
        self.service = service or AIService()

    def detect(self, listing: dict[str, Any]) -> List[OpportunityFactor]:
        factors = []

        # We can either use pre-calculated AI data from the listing dict
        # or call the service directly if it's missing.

        ai_data = listing.get("ai_opportunity_data")
        if not ai_data and self.service and settings.ai_enabled:
            try:
                ai_data = self.service.discover_opportunities(
                    listing.get("title", ""), listing.get("description", "")
                )
            except Exception:
                return []

        if not ai_data:
            return []

        if getattr(ai_data, "has_misspellings", False):
            factors.append(
                OpportunityFactor(
                    name="ai_misspellings",
                    score_impact=20,
                    reason="AI detected misspellings that might hide this from other buyers.",
                    category="Metadata",
                )
            )

        if getattr(ai_data, "is_wrong_category", False):
            factors.append(
                OpportunityFactor(
                    name="ai_wrong_category",
                    score_impact=25,
                    reason="AI suggests this listing is in a suboptimal category.",
                    category="Metadata",
                )
            )

        if getattr(ai_data, "poor_photos", False):
            factors.append(
                OpportunityFactor(
                    name="ai_poor_photos",
                    score_impact=15,
                    reason="AI flagged the photos as low quality, potentially lowering competition.",
                    category="Listing Quality",
                )
            )

        return factors


# Default Engine Configuration
DEFAULT_DETECTORS = [
    ListingQualityDetector(),
    MetadataDetector(),
    MarketSignalsDetector(),
    SpecializationDetector(),
    SellerMotivationDetector(),
    AIDetector(),
]


def analyze_opportunity(listing: dict[str, Any]) -> OpportunityResult:
    """Convenience function to analyze a listing using the default opportunity engine."""
    engine = OpportunityEngine(DEFAULT_DETECTORS)
    return engine.analyze(listing)
