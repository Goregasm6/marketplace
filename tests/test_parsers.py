from pathlib import Path
from collectors.parsers.craigslist import CraigslistParser


def test_craigslist_parser_with_fixture():
    fixture_path = Path(__file__).parent / "fixtures" / "craigslist_search.html"
    html = fixture_path.read_text(encoding="utf-8")

    parser = CraigslistParser()
    items = parser.parse(html)

    assert len(items) == 3

    assert items[0]["title"] == "Vintage Camera"
    assert items[0]["url"] == "https://sfbay.craigslist.org/sfc/ele/7700000001.html"
    assert items[0]["price"] == "$50"

    assert items[1]["title"] == "Modern Laptop"
    assert items[1]["url"] == "https://sfbay.craigslist.org/sfc/ele/7700000002.html"
    assert items[1]["price"] == "$500"

    assert items[2]["title"] == "Broken Toaster"
    assert items[2]["url"] == "https://sfbay.craigslist.org/sfc/ele/7700000003.html"
    assert items[2]["price"] == "$5"


def test_craigslist_parser_empty_html():
    parser = CraigslistParser()
    items = parser.parse("")
    assert items == []


def test_craigslist_parser_no_results():
    parser = CraigslistParser()
    items = parser.parse("<html><body><p>No results found</p></body></html>")
    assert items == []
