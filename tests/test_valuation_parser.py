import pytest

from analysis.valuation.parser import detect_category, extract_brand, extract_model, normalize_title, parse_listing


def test_normalize_title_removes_case_punctuation_and_accents() -> None:
    assert normalize_title("  SÓNY—WH-1000XM4!! ") == "sony wh 1000xm4"


def test_parser_extracts_brand_model_category_and_keywords() -> None:
    parsed = parse_listing({"title": "Apple iPhone 13 Pro - excellent", "price": 425})

    assert parsed.recognized_brand == "Apple"
    assert parsed.recognized_model == "iPhone 13 Pro"
    assert parsed.category == "electronics"
    assert "iphone" in parsed.matched_keywords
    assert parsed.asking_price == 425


def test_parser_accepts_attribute_based_listing() -> None:
    class Listing:
        title = "Sony WH-1000XM4 headphones"
        description = "Like new"
        price = 175

    parsed = parse_listing(Listing())
    assert parsed.recognized_brand == "Sony"
    assert parsed.recognized_model == "WH-1000XM4"


def test_parser_supports_custom_brand_and_category_catalogs() -> None:
    parsed = parse_listing(
        {"title": "Acme ZX-9 Road Bicycle"},
        brands=("Acme",),
        category_keywords={"bicycles": ("bicycle", "road")},
    )

    assert parsed.recognized_brand == "Acme"
    assert parsed.recognized_model == "ZX-9"
    assert parsed.category == "bicycles"
    assert parsed.matched_keywords == ["bicycle", "road"]


def test_recognition_helpers_return_empty_results_without_signals() -> None:
    assert extract_brand("Unbranded wooden chair") is None
    assert extract_model("Unbranded wooden chair") is None
    assert detect_category("Unbranded wooden chair") == (None, [])


def test_parser_requires_a_title() -> None:
    with pytest.raises(ValueError, match="title"):
        parse_listing({"price": 10})
