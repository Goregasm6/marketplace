from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from analysis.keywords import keyword_score


@dataclass(frozen=True)
class RuleResult:
    """Outcome of a single scoring rule."""

    name: str
    points: float
    reason: str


class ScoringRule:
    """Base interface for an individual FlipScore rule."""

    name = "rule"
    description = "Base scoring rule"

    def apply(self, listing: dict[str, Any]) -> RuleResult:
        raise NotImplementedError


class PriceRule(ScoringRule):
    """Rewards listings that appear to be priced aggressively for a flip."""

    name = "price"
    description = "Rewards lower prices because they leave more room for profit."

    def apply(self, listing: dict[str, Any]) -> RuleResult:
        price = float(listing.get("price", 0) or 0)
        if price < 100:
            return RuleResult(self.name, 25, "Price is very low, which leaves room for profit.")
        if price < 200:
            return RuleResult(self.name, 12, "Price is low enough to support a healthy margin.")
        if price < 400:
            return RuleResult(self.name, 4, "Price is moderate but still manageable.")
        return RuleResult(self.name, 0, "Price is high enough that margin may be compressed.")


class CategoryRule(ScoringRule):
    """Rewards categories that tend to be frequent flip opportunities."""

    name = "category"
    description = "Rewards categories that are known to be good flip candidates."

    def apply(self, listing: dict[str, Any]) -> RuleResult:
        category = str(listing.get("category", "") or "").strip().lower()
        if category in {"electronics", "games", "collectibles", "home goods"}:
            return RuleResult(self.name, 15, f"Category '{category}' is a strong flip category.")
        if category in {"tools", "apparel", "furniture"}:
            return RuleResult(self.name, 8, f"Category '{category}' has some flip demand.")
        return RuleResult(self.name, 0, "Category is not clearly associated with strong flip demand.")


class KeywordRule(ScoringRule):
    """Rewards listings with strong keyword matches from the keyword analysis module."""

    name = "keyword"
    description = "Rewards listings that match high-value keywords."

    def apply(self, listing: dict[str, Any]) -> RuleResult:
        keyword_score_value = listing.get("keyword_score")
        if keyword_score_value is None:
            text = " ".join(
                [str(listing.get("title", "") or ""), str(listing.get("description", "") or "")]
            ).strip()
            keyword_score_value = keyword_score(text) if text else 0

        if keyword_score_value >= 70:
            return RuleResult(self.name, 20, "Keyword score is strong, suggesting the listing aligns with demand.")
        if keyword_score_value >= 40:
            return RuleResult(self.name, 10, "Keyword score is moderate and may indicate a good fit.")
        return RuleResult(self.name, 0, "Keyword score is weak, so the listing is less likely to be attractive.")


class BrandRule(ScoringRule):
    """Rewards strong brand signals because premium brand names often sell faster."""

    name = "brand"
    description = "Rewards listings with strong brand recognition."

    def apply(self, listing: dict[str, Any]) -> RuleResult:
        brand_score_value = float(listing.get("brand_score", 0) or 0)
        if brand_score_value >= 80:
            return RuleResult(self.name, 15, "Brand score is strong, which should improve resale demand.")
        if brand_score_value >= 60:
            return RuleResult(self.name, 8, "Brand score is decent and adds some confidence.")
        return RuleResult(self.name, 0, "Brand score is not strong enough to boost the valuation.")


class DistanceRule(ScoringRule):
    """Rewards listings that are close enough to be practical to inspect or collect."""

    name = "distance"
    description = "Rewards nearby listings because they are easier to acquire."

    def apply(self, listing: dict[str, Any]) -> RuleResult:
        distance = float(listing.get("distance", 999) or 999)
        if distance <= 5:
            return RuleResult(self.name, 10, "Distance is close, so the pickup is practical.")
        if distance <= 15:
            return RuleResult(self.name, 5, "Distance is reasonable and still manageable.")
        return RuleResult(self.name, 0, "Distance is far, which increases friction.")


class ListingAgeRule(ScoringRule):
    """Rewards fresh listings because they are less stale and may have better urgency."""

    name = "listing_age"
    description = "Rewards recent listings that have not gone stale."

    def apply(self, listing: dict[str, Any]) -> RuleResult:
        age = float(listing.get("listing_age", 999) or 999)
        if age <= 2:
            return RuleResult(self.name, 8, "Listing is recent, which is usually a better signal.")
        if age <= 7:
            return RuleResult(self.name, 4, "Listing is somewhat recent and may still be active.")
        return RuleResult(self.name, 0, "Listing is old enough that the window may be closing.")


class SellerMotivationRule(ScoringRule):
    """Rewards listings where the seller signals urgency or a strong reason to sell."""

    name = "seller_motivation"
    description = "Rewards seller urgency because motivated sellers often accept lower offers."

    def apply(self, listing: dict[str, Any]) -> RuleResult:
        motivation = str(listing.get("seller_motivation", "") or "").strip().lower()
        if any(term in motivation for term in ["must sell", "urgent", "moving", "cash", "urgently"]):
            return RuleResult(self.name, 8, "Seller appears motivated, which may support a lower offer.")
        if motivation:
            return RuleResult(self.name, 3, "Seller motivation is present but not clearly urgent.")
        return RuleResult(self.name, 0, "No seller motivation signal was provided.")


class RepairIndicatorsRule(ScoringRule):
    """Penalizes listings with obvious repair issues that reduce resale confidence."""

    name = "repair_indicators"
    description = "Penalizes visible damage or repair concerns."

    def apply(self, listing: dict[str, Any]) -> RuleResult:
        indicators = listing.get("repair_indicators", []) or []
        if isinstance(indicators, str):
            indicators = [indicators]

        if not indicators:
            return RuleResult(self.name, 0, "No repair indicators were observed.")

        normalized = [str(item).strip().lower() for item in indicators if str(item).strip()]
        if any(keyword in " ".join(normalized) for keyword in ["cracked", "broken", "battery", "water", "screen", "repair"]):
            return RuleResult(self.name, -8, "Repair indicators suggest the item may need work or have reduced resale value.")
        return RuleResult(self.name, -2, "Some concerns were noted, though they are not clearly repair-related.")


DEFAULT_RULES: tuple[ScoringRule, ...] = (
    PriceRule(),
    CategoryRule(),
    KeywordRule(),
    BrandRule(),
    DistanceRule(),
    ListingAgeRule(),
    SellerMotivationRule(),
    RepairIndicatorsRule(),
)


def evaluate_listing(listing: dict[str, Any], rules: Iterable[ScoringRule] | None = None) -> dict[str, Any]:
    """Evaluate a listing and return a score, confidence, and human-readable reasons."""

    rule_list = tuple(rules or DEFAULT_RULES)
    results = [rule.apply(listing) for rule in rule_list]
    total_points = sum(result.points for result in results)
    score = max(0, min(100, int(round(50 + total_points))))

    active_results = [result for result in results if result.points != 0]
    signal_count = len(active_results)
    field_count = sum(1 for key in listing if listing.get(key) not in (None, "", [], {}, ()) and key not in {"title", "description"})
    confidence = min(1.0, 0.35 + 0.08 * signal_count + 0.01 * field_count)

    reasons = [result.reason for result in results if result.reason]
    return {
        "score": score,
        "confidence": round(confidence, 2),
        "reasons": reasons,
    }


def calculate(listing: dict[str, Any], rules: Iterable[ScoringRule] | None = None) -> dict[str, Any]:
    """Backward-compatible wrapper around the modular evaluator."""

    return evaluate_listing(listing, rules=rules)
