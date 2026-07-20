import pytest

from analysis.valuation import (
    ComparableProduct,
    InMemoryPricingProvider,
    ValuationEngine,
    estimate_value,
)
from analysis.valuation.confidence import calculate_confidence


def _provider() -> InMemoryPricingProvider:
    return InMemoryPricingProvider(
        [
            ComparableProduct(
                title="Apple iPhone 13 Pro 128GB",
                price=500,
                brand="Apple",
                category="electronics",
            ),
            ComparableProduct(
                title="Apple iPhone 13 Pro unlocked",
                price=550,
                brand="Apple",
                category="electronics",
            ),
            ComparableProduct(
                title="Apple iPhone 13 Pro excellent condition",
                price=525,
                brand="Apple",
                category="electronics",
            ),
            ComparableProduct(
                title="Nintendo Switch console",
                price=200,
                brand="Nintendo",
                category="gaming",
            ),
        ]
    )


def test_engine_returns_required_valuation_fields_using_median_and_resale_rate() -> (
    None
):
    result = ValuationEngine([_provider()]).value(
        {"title": "Apple iPhone 13 Pro", "price": 300}
    )

    assert result.estimated_market_value == 525
    assert result.estimated_resale_value == 446.25
    assert 0 < result.confidence <= 1
    assert result.recognized_brand == "Apple"
    assert result.recognized_model == "iPhone 13 Pro"
    assert "iphone" in result.matched_keywords
    assert any("median" in reason for reason in result.reasoning)


def test_engine_combines_multiple_providers_without_provider_specific_logic() -> None:
    first = InMemoryPricingProvider(
        [
            ComparableProduct(
                title="Sony WH-1000XM4", price=180, brand="Sony", category="electronics"
            )
        ]
    )
    second = InMemoryPricingProvider(
        [
            ComparableProduct(
                title="Sony WH-1000XM4 headphones",
                price=220,
                brand="Sony",
                category="electronics",
            )
        ]
    )

    result = ValuationEngine([first, second], resale_rate=0.9).value(
        {"title": "Sony WH-1000XM4 headphones"}
    )

    assert result.estimated_market_value == 200
    assert result.estimated_resale_value == 180


def test_engine_returns_unknown_values_and_zero_confidence_when_no_comparable_matches() -> (
    None
):
    result = ValuationEngine([_provider()]).value(
        {"title": "Handmade oak dining table"}
    )

    assert result.estimated_market_value is None
    assert result.estimated_resale_value is None
    assert result.confidence == 0
    assert any("No sufficiently" in reason for reason in result.reasoning)


def test_convenience_function_and_constructor_validation() -> None:
    result = estimate_value({"title": "Apple iPhone 13 Pro"}, [_provider()])
    assert result.estimated_market_value == 525

    with pytest.raises(ValueError, match="resale_rate"):
        ValuationEngine(resale_rate=0)


def test_confidence_rewards_better_samples_and_is_bounded() -> None:
    weak = calculate_confidence(match_scores=[0.4], prices=[100], recognized=False)
    strong = calculate_confidence(
        match_scores=[0.9, 0.9, 0.9, 0.9, 0.9],
        prices=[100, 101, 99, 100, 100],
        recognized=True,
    )

    assert 0 <= weak < strong <= 1
