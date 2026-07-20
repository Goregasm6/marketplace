from .base import CategoryKnowledge, MarginRange, ShippingProfile


class PowerToolsCategory(CategoryKnowledge):
    name = slug = "power-tools"
    description = "Cordless and corded trade power tools, batteries, and kits."
    brands = ("DeWalt", "Milwaukee", "Makita", "Festool", "Bosch", "Ridgid", "Hilti")
    keywords = (
        "drill",
        "impact driver",
        "circular saw",
        "miter saw",
        "battery",
        "tool kit",
        "compressor",
    )
    common_misspellings = ("dewalt", "milwauke", "makitta", "sawzall")
    seasonality = "Spring and summer renovation season are strongest; contractor demand remains steady."
    repair_opportunities = (
        "battery recell",
        "brush replacement",
        "switch repair",
        "chuck replacement",
    )
    shipping_profile = ShippingProfile(
        "medium",
        "insured ground parcel",
        "Ship batteries compliantly and test chargers before listing.",
    )
    typical_margins = MarginRange(0.20, 0.45)
    pricing_providers = ("eBay sold listings", "Acme Tools", "Toolup")
    common_model_prefixes = ("DCD", "M18", "XDT", "TS")
    related_categories = ("industrial", "home-improvement")
