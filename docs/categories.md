# Category knowledge modules

Categories are plugins in the `categories` package. Each module owns the
market knowledge for one category, so classification, scoring, and future
pricing workflows do not need a central category switch statement.

The built-in modules cover electronics, guitars, servers, cameras, industrial
equipment, medical equipment, networking, power tools, gaming, audio, watches,
and laboratory equipment. They are discovered automatically by
`PluginLoader`, and are also available through `categories.get_categories()`.

## What a module declares

Every category subclasses `CategoryKnowledge` and declares:

- `brands`, `keywords`, and `common_misspellings` for recognition
- `seasonality` and `repair_opportunities` for sourcing and review
- `shipping_profile` for handling constraints
- `typical_margins` as a `MarginRange(low, high)` before fees and labor
- `pricing_providers` for comparable-sale research
- `common_model_prefixes` for model recognition
- `related_categories` for expansion and routing

The valuation parser builds its default brands and category keywords from
these modules. FlipScore uses the module's typical margin rather than a
hardcoded list of favored category names.

## Add a category

1. Add `categories/<slug>.py`.
2. Create one `CategoryKnowledge` subclass; set both `name` and `slug` to the
   stable, lowercase category identifier (hyphens are preferred).
3. Fill every knowledge field with evidence-based terms and providers. Keep
   misspellings specific enough to avoid matching unrelated listings.
4. Run `uv run pytest` (or the project test command). Discovery will load the
   new module automatically—do not add it to a central registry.

```python
from .base import CategoryKnowledge, MarginRange, ShippingProfile


class BicyclesCategory(CategoryKnowledge):
    name = slug = "bicycles"
    description = "Bicycles, frames, wheels, and components."
    brands = ("Trek", "Specialized")
    keywords = ("bicycle", "road bike", "mountain bike")
    common_misspellings = ("specializedd",)
    seasonality = "Highest demand in spring and early summer."
    repair_opportunities = ("tune-up", "cable replacement")
    shipping_profile = ShippingProfile("oversize", "bike box or local pickup", "Protect the derailleur.")
    typical_margins = MarginRange(0.20, 0.45)
    pricing_providers = ("eBay sold listings", "Pinkbike")
    common_model_prefixes = ("Domane", "Stumpjumper")
    related_categories = ("power-tools",)
```

Use a new module rather than extending an unrelated category. If a listing can
reasonably match two categories, add distinctive keywords or brands so the
most specific module wins during recognition.
