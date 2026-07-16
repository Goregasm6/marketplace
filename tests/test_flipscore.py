from analysis.flipscore import (
    PriceScore,
    DemandScore,
    SellerScore,
    RiskScore,
    DistanceScore,
    RepairScore,
    evaluate_listing,
)


def test_price_score_rewards_low_price() -> None:
    result = PriceScore().calculate({"price": 79})

    assert result.score == 100
    assert "very low" in result.explanation.lower()


def test_demand_score_evaluates_signals() -> None:
    # Testing with keyword and brand signals
    result = DemandScore().calculate({"keyword_score": 85, "brand_score": 90})

    assert result.score >= 60
    assert "keyword" in result.explanation.lower()
    assert "brand" in result.explanation.lower()


def test_seller_score_rewards_motivation_and_freshness() -> None:
    result = SellerScore().calculate({"seller_motivation": "must sell urgently", "listing_age": 1})

    assert result.score > 50
    assert "motivated" in result.explanation.lower()
    assert "fresh" in result.explanation.lower()


def test_risk_score_detects_risk_factors() -> None:
    result = RiskScore().calculate({"repair_indicators": ["cracked screen"], "description": "as is untested"})

    assert result.score < 50
    assert "repair" in result.explanation.lower()
    assert "risk" in result.explanation.lower()


def test_distance_score_rewards_proximity() -> None:
    result = DistanceScore().calculate({"distance": 3})

    assert result.score == 100
    assert "close" in result.explanation.lower()


def test_repair_score_evaluates_repair_need() -> None:
    result = RepairScore().calculate({"repair_indicators": ["broken screen"]})

    assert result.score == 20
    assert "significant" in result.explanation.lower()


def test_evaluate_listing_returns_modular_results() -> None:
    listing = {
        "price": 89,
        "category": "electronics",
        "keyword_score": 82,
        "brand_score": 88,
        "distance": 3,
        "listing_age": 1,
        "seller_motivation": "must sell urgently",
        "repair_indicators": [],
    }
    
    result = evaluate_listing(listing)

    assert 0 <= result["score"] <= 100
    assert 0.0 <= result["confidence"] <= 1.0
    assert "component_scores" in result
    assert "price" in result["component_scores"]
    assert "demand" in result["component_scores"]
    assert "seller" in result["component_scores"]
    assert len(result["reasons"]) > 0


def test_custom_weights_affect_score() -> None:
    listing = {"price": 500, "distance": 2} # High price (bad), Close (good)
    
    # Weight price heavily
    res1 = evaluate_listing(listing, weights={"price": 10.0, "distance": 0.1})
    
    # Weight distance heavily
    res2 = evaluate_listing(listing, weights={"price": 0.1, "distance": 10.0})
    
    assert res1["score"] < res2["score"]
