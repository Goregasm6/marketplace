# Opportunity Discovery Engine

The Opportunity Discovery Engine is a specialized component of MAIE designed to identify "hidden" value in marketplace listings. Unlike traditional scrapers that only look at price, this engine detects factors that might deter average buyers but represent high potential for experienced arbitrageurs.

## Key Features

- **OpportunityScore**: A metric (0-100) that estimates the "hidden value" of a listing, independent of its FlipScore.
- **Detailed Explanations**: Every detected opportunity is accompanied by a clear reason why it adds value.
- **Extensible Architecture**: New opportunity detectors can be added as plugins.
- **AI-Powered Detection**: Leverages LLMs to detect subtle signals like misspellings, wrong categories, and poor listing quality.

## Detected Opportunities

The engine currently detects the following types of opportunities:

### Listing Quality
- **Poor Photos**: Low quality or very few photos that might hide the true condition/value.
- **Generic Titles**: Vague titles like "stuff" or "box of items" that are hard to find.
- **Incomplete Descriptions**: Minimal text that discourages others from inquiring.

### Metadata Issues
- **Misspellings**: Typos in brand names or product types (e.g., "Iphone" instead of "iPhone").
- **Wrong Category**: Items listed in the wrong marketplace category, reducing visibility.
- **Missing Model Numbers**: Listings that omit specific model numbers, making them harder for pros to value accurately.

### Market Signals
- **Bundle Listings**: Collections of items sold together, often at a lower per-item price.
- **Seasonality**: Off-season items that can be bought low and sold high later.
- **Historical Price Drops**: Listings where the seller has recently lowered the price, indicating high motivation.

### Specialized Equipment
- **Rare Brands**: High-value niche brands with low general awareness.
- **Industrial Surplus**: Equipment from labs, hospitals, or factories.
- **Commercial Equipment**: High-value tools and machines for professional use.

### Seller Motivation
- **High Motivation**: Keywords indicating the seller needs to move quickly (e.g., "moving", "must sell").
- **Repair Opportunities**: Items needing minor repairs that can be acquired at a steep discount.

## How it Works

The engine runs a pipeline of `OpportunityDetector` plugins. Each detector analyzes the listing and returns a set of `OpportunityFactor` objects. These factors are then aggregated into an `OpportunityResult`.

### Example Usage

```python
from analysis.opportunity import analyze_opportunity

listing = {
    "title": "Old guitar and amp",
    "description": "Moving soon, must sell everything. Amp needs new tube.",
    "price": 100,
    "images": ["image1.jpg"]
}

result = analyze_opportunity(listing)

print(f"Opportunity Score: {result.opportunity_score}")
print(f"Explanation: {result.explanation}")
```

## Adding Custom Detectors

To add a new detector, inherit from `OpportunityDetector` and implement the `detect` method:

```python
from analysis.opportunity import OpportunityDetector, OpportunityFactor

class LocalHolidayDetector(OpportunityDetector):
    def detect(self, listing):
        factors = []
        # Custom logic here
        return factors
```
