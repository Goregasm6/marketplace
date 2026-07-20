from unittest.mock import MagicMock
from analysis.opportunity import (
    analyze_opportunity,
    ListingQualityDetector,
    MetadataDetector,
    MarketSignalsDetector,
    SellerMotivationDetector,
    AIDetector,
)
from core.ai.parser import OpportunityAnalysisResponse


def test_listing_quality_detector():
    detector = ListingQualityDetector()

    # Test poor photos
    listing = {
        "title": "Good Title",
        "description": "Long enough description here to avoid that trigger.",
        "images": ["1"],
    }
    factors = detector.detect(listing)
    assert any(f.name == "few_photos" for f in factors)

    # Test generic title
    listing = {
        "title": "stuff",
        "description": "Long enough description here to avoid that trigger.",
        "images": ["1", "2"],
    }
    factors = detector.detect(listing)
    assert any(f.name == "generic_title" for f in factors)


def test_metadata_detector():
    detector = MetadataDetector()

    # Test missing model number
    listing = {"title": "Just a guitar", "description": "Some description"}
    factors = detector.detect(listing)
    assert any(f.name == "missing_model_number" for f in factors)

    # Test with model number
    listing = {
        "title": "Fender Stratocaster American Professional II",
        "description": "Serial number 12345",
    }
    factors = detector.detect(listing)
    assert not any(f.name == "missing_model_number" for f in factors)


def test_market_signals_detector():
    detector = MarketSignalsDetector()

    # Test bundle
    listing = {
        "title": "Camera bundle with lenses",
        "description": "Everything must go",
    }
    factors = detector.detect(listing)
    assert any(f.name == "bundle_listing" for f in factors)


def test_seller_motivation_detector():
    detector = SellerMotivationDetector()

    # Test motivation
    listing = {"title": "TV", "description": "Moving soon, must sell!"}
    factors = detector.detect(listing)
    assert any(f.name == "high_seller_motivation" for f in factors)

    # Test repair
    listing = {"title": "iPhone", "description": "Screen is cracked, but works."}
    factors = detector.detect(listing)
    assert any(f.name == "repair_opportunity" for f in factors)


def test_ai_detector_with_precalculated_data():
    detector = AIDetector(service=None)

    ai_data = OpportunityAnalysisResponse(
        has_misspellings=True,
        is_wrong_category=True,
        missing_model_number=True,
        is_bundle=True,
        poor_photos=True,
        explanation="AI detected everything",
        detected_factors=["misspellings", "wrong_category"],
    )

    listing = {"ai_opportunity_data": ai_data}
    factors = detector.detect(listing)

    assert any(f.name == "ai_misspellings" for f in factors)
    assert any(f.name == "ai_wrong_category" for f in factors)


def test_full_engine_analysis(monkeypatch):
    # Mock AIService to avoid network calls and timeouts
    mock_service = MagicMock()
    monkeypatch.setattr("analysis.opportunity.AIService", lambda: mock_service)

    listing = {
        "title": "box of stuff",
        "description": "Moving tomorrow. Need cash. Most things work but some need repair.",
        "price": 50,
        "images": [],
    }

    result = analyze_opportunity(listing)

    assert result.opportunity_score > 50
    assert len(result.factors) >= 3
    assert any("title" in f.reason.lower() for f in result.factors)
    assert any("urgency" in f.reason.lower() for f in result.factors)
