from analysis.valuation.comparables import ComparableProduct
from analysis.valuation.matcher import find_matches, match_score
from analysis.valuation.parser import parse_listing


def test_model_and_brand_match_receive_strong_score() -> None:
    listing = parse_listing({"title": "Sony WH-1000XM4 Headphones"})
    comparable = ComparableProduct(title="Sony WH-1000XM4 wireless headphones", price=200, brand="Sony", category="electronics")

    score, keywords = match_score(listing, comparable)

    assert score > 0.8
    assert "sony" in keywords


def test_find_matches_excludes_unrelated_products_and_sorts_results() -> None:
    listing = parse_listing({"title": "Apple iPhone 13 Pro"})
    products = [
        ComparableProduct(title="Apple iPhone 13 Pro 128GB", price=500, brand="Apple", category="electronics"),
        ComparableProduct(title="Apple iPhone 13", price=400, brand="Apple", category="electronics"),
        ComparableProduct(title="DeWalt cordless drill", price=80, brand="DeWalt", category="tools"),
    ]

    matches = find_matches(listing, products)

    assert [match.comparable.price for match in matches] == [500, 400]
