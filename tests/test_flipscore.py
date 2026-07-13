from analysis.flipscore import (
    CategoryRule,
    DistanceRule,
    ListingAgeRule,
    PriceRule,
    RepairIndicatorsRule,
    SellerMotivationRule,
    evaluate_listing,
)


def test_price_rule_rewards_low_price() -> None:
    result = PriceRule().apply({"price": 79})

    assert result.points == 25
    assert "very low" in result.reason.lower()


def test_category_rule_rewards_common_flip_categories() -> None:
    result = CategoryRule().apply({"category": "electronics"})

    assert result.points == 15
    assert "electronics" in result.reason.lower()


def test_keyword_rule_rewards_strong_keyword_match() -> None:
    result = evaluate_listing({"keyword_score": 85})

    assert result["score"] >= 20
    assert any("keyword" in reason.lower() for reason in result["reasons"])


def test_brand_rule_rewards_strong_brand_signal() -> None:
    result = evaluate_listing({"brand_score": 90})

    assert result["score"] >= 15
    assert any("brand" in reason.lower() for reason in result["reasons"])


def test_distance_rule_rewards_close_listings() -> None:
    result = DistanceRule().apply({"distance": 4})

    assert result.points == 10
    assert "close" in result.reason.lower()


def test_listing_age_rule_rewards_recent_listings() -> None:
    result = ListingAgeRule().apply({"listing_age": 2})

    assert result.points == 8
    assert "recent" in result.reason.lower()


def test_seller_motivation_rule_rewards_high_motivation() -> None:
    result = SellerMotivationRule().apply({"seller_motivation": "must sell urgently"})

    assert result.points == 8
    assert "motivated" in result.reason.lower()


def test_repair_indicators_rule_penalizes_obvious_repairs() -> None:
    result = RepairIndicatorsRule().apply({"repair_indicators": ["cracked screen", "battery issue"]})

    assert result.points == -8
    assert "repair" in result.reason.lower()


def test_evaluate_listing_returns_confidence_and_reasons() -> None:
    result = evaluate_listing(
        {
            "price": 89,
            "category": "electronics",
            "keyword_score": 82,
            "brand_score": 88,
            "distance": 3,
            "listing_age": 1,
            "seller_motivation": "must sell urgently",
            "repair_indicators": [],
        }
    )

    assert 0 <= result["score"] <= 100
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["reasons"]
