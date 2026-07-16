import pytest
from analysis.search import SearchGenerator
from categories.base import CategoryKnowledge, ShippingProfile, MarginRange

@pytest.fixture
def mock_category():
    class MockCategory(CategoryKnowledge):
        slug = "test-category"
        brands = ("Sony", "Marantz")
        keywords = ("Vintage", "Hi-Fi")
        common_misspellings = ("Maranz", "Sonee")
        common_model_prefixes = ("STR-", "TA-")
        repair_opportunities = ("Needs Recap",)
    
    return MockCategory()

def test_basic_search_generation():
    generator = SearchGenerator()
    queries = generator.generate("Marantz Receiver")
    
    assert "marantz receiver" in queries
    # Check for abbreviation
    assert "marantz rcvr" in queries
    # Check for plural
    assert "marantz receivers" in queries
    # Check for brand alias
    assert "maranz receiver" in queries

def test_category_specific_expansion(mock_category):
    generator = SearchGenerator(category=mock_category)
    queries = generator.generate("Amplifier")
    
    assert "amplifier" in queries
    # Check for category brands
    assert "amplifier sony" in queries
    assert "amplifier marantz" in queries
    # Check for category keywords
    assert "amplifier vintage" in queries
    # Check for model prefixes
    assert "amplifier str-" in queries

def test_modifiers():
    generator = SearchGenerator()
    queries = generator.generate("Guitar")
    
    assert "guitar repair" in queries
    assert "guitar bundle" in queries
    assert "guitar must go" in queries

def test_misspellings_from_category(mock_category):
    generator = SearchGenerator(category=mock_category)
    queries = generator.generate("Marantz")
    
    assert "maranz" in queries

def test_pluralization_rules():
    generator = SearchGenerator()
    
    # -y to -ies
    assert "categories" in generator._expand_token("category")
    # -s to -ses
    assert "buses" in generator._expand_token("bus")
    # regular -s
    assert "guitars" in generator._expand_token("guitar")

def test_max_queries_limit():
    generator = SearchGenerator()
    queries = generator.generate("Sony Marantz Receiver Amplifier Speaker", max_queries=5)
    
    assert len(queries) <= 5

def test_foreign_spellings():
    generator = SearchGenerator()
    queries = generator.generate("Analog Meter")
    
    assert "analogue meter" in queries
    assert "analog metre" in queries
