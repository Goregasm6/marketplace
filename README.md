# Marketplace Arbitrage Intelligence Engine (MAIE)

MAIE is an open-source Python project for monitoring online marketplaces, identifying arbitrage opportunities, and surfacing actionable insights through a modular, testable architecture.

## Vision

The long-term goal of MAIE is to provide a reliable foundation for collecting marketplace data, analyzing listing quality, and supporting alerting and dashboard workflows. The project is designed to stay maintainable as it grows by emphasizing clean architecture, strong typing, and clear separation of concerns.

## Architecture Overview

The repository is organized around a layered architecture:

- app: application entry points and CLI wiring
- core: shared domain logic and reusable abstractions
- collectors: adapters for gathering data from marketplaces
- analysis: scoring, classification, and enrichment logic
- categories: domain-specific category handling
- database: persistence and schema definitions
- alerts: notification integrations
- dashboard: optional UI or reporting components
- config: environment and application configuration
- data: local sample data and fixtures
- docs: documentation and design notes
- logs: runtime log storage
- models: shared data models and schemas
- tests: automated tests
- scripts: operational helper scripts

## Requirements

- Python 3.12+
- uv for dependency management
- SQLModel for persistence models
- Pydantic v2 for configuration
- Loguru for logging
- Typer for CLI
- pytest for testing

## Setup

1. Install uv if it is not already available:
   - https://docs.astral.sh/uv/
2. Create and activate a virtual environment:
   - `uv venv`
   - `source .venv/bin/activate`
3. Install dependencies:
   - `uv pip install -e ".[dev]"`
4. Copy the example environment file:
   - `cp .env.example .env`

## Configuration

MAIE loads configuration from a local .env file using Pydantic Settings. Every option below is documented and validated with helpful error messages.

- SQLITE_PATH: Path to the SQLite database file. Defaults to database/listings.db inside the project root.
- SEARCH_INTERVAL: How often searches should run, in minutes. Defaults to 15.
- SEARCH_RADIUS: Maximum search radius in miles. Defaults to 25.
- DISCORD_WEBHOOK: Optional Discord webhook URL used to send alerts.
- TELEGRAM_TOKEN: Optional Telegram bot token used to send alerts.
- MINIMUM_FLIPSCORE: Minimum FlipScore required for an opportunity to be surfaced. Defaults to 60.
- MINIMUM_EXPECTED_PROFIT: Minimum expected profit in dollars required for a listing to be considered. Defaults to 20.0.
- LOGGING_LEVEL: Logging verbosity. Supported values are DEBUG, INFO, WARNING, ERROR, and CRITICAL.
- ENABLED_COLLECTORS: Comma-separated list of collectors to enable. Defaults to craigslist.
- ENABLED_CATEGORIES: Comma-separated list of categories to enable. Defaults to electronics,tools.

A sample environment file is available in .env.example.

## Development Workflow

- Run the CLI entry point:
  - `uv run maie --help`
- Run tests:
  - `make test`
- Format code:
  - `make format`
- Lint code:
  - `make lint`

## Coding Standards

- Favor small, focused modules with clear responsibilities.
- Keep business logic out of CLI and infrastructure layers.
- Prefer explicit configuration over hidden defaults.
- Write tests for new behavior as it is introduced.
- Document public interfaces and configuration options.
- Preserve backward compatibility whenever possible.

## Project Status

This repository currently contains initial scaffolding only. Business logic and production integrations will be added incrementally.

## Collector Framework

The collector framework lives in [collectors/base.py](collectors/base.py). It defines a generic base interface for marketplace integrations that can be extended without changing the existing collector registry logic.

Every concrete collector should:

- inherit from BaseCollector
- implement search(), fetch(), normalize(), validate(), and save()
- expose a unique name or rely on the class name as the registry key

To add a new collector:

1. Create a new module in the collectors package, for example collectors/example.py.
2. Define a subclass of BaseCollector and implement the required methods.
3. Import the module once so the subclass is registered, or rely on discovery when the package is scanned.
4. Use the collector through its class or registry name.

The framework is intentionally generic and does not implement any marketplace-specific behavior.

## Domain Model

The core persistence model for MAIE is now defined in [database/models.py](database/models.py) and documented in [docs/domain-models.md](docs/domain-models.md). It introduces the main entities for listings, sellers, searches, images, price history, opportunities, and purchases.

The design emphasizes:

- UUID primary keys for identity and eventual cross-system compatibility
- created_at and updated_at timestamps for auditability
- explicit relationships between listings and their related entities
- indexed fields for the most common lookup paths
- a separation between persistence models and future application/service-layer logic

## FlipScore

FlipScore is the first-pass opportunity scorer for marketplace listings. It evaluates a listing with a modular rule framework so new scoring rules can be added by creating a new rule class and registering it in the default rule list.

### Inputs

The evaluator accepts the following signals:

- price
- category
- keyword_score
- brand_score
- distance
- listing_age
- seller_motivation
- repair_indicators

### Scoring rules

Each rule contributes points and a human-readable explanation:

- PriceRule: rewards listings priced below $100 with +25 points, below $200 with +12 points, and below $400 with +4 points.
- CategoryRule: adds +15 points for strong flip categories such as electronics, games, collectibles, and home goods; +8 points for moderately relevant categories like tools, apparel, and furniture.
- KeywordRule: adds +20 points for keyword scores above 70, +10 points for scores above 40, and 0 otherwise.
- BrandRule: adds +15 points for strong brand scores above 80, +8 points for scores above 60, and 0 otherwise.
- DistanceRule: adds +10 points for distances at or below 5 miles, +5 points for distances at or below 15 miles, and 0 beyond that.
- ListingAgeRule: adds +8 points for listings that are 2 days old or newer, +4 points for listings up to 7 days old, and 0 after that.
- SellerMotivationRule: adds +8 points when the seller appears highly motivated, +3 points for some motivation, and 0 when no signal exists.
- RepairIndicatorsRule: subtracts 8 points for obvious repair or damage signals and 2 points for weaker concerns.

### Output

The evaluator returns:

- score: an integer between 0 and 100
- confidence: a float between 0.0 and 1.0
- reasons: a list of human-readable explanations for each rule that contributed a signal

To extend the scorer, define a new subclass of ScoringRule, implement its apply() method, and include it in the DEFAULT_RULES tuple.
