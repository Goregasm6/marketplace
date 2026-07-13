# ADR 0003: Use plugin-based collectors

- Status: Accepted
- Date: 2026-07-13

## Context
Marketplace integrations differ in format, rate limits, and data quality. We want to support new sources without rewriting the application shell every time.

## Decision
Model each marketplace integration as a collector plugin that implements a shared interface and can be registered or discovered by the application.

## Consequences
- Pros: isolation, easier testing, and simpler addition of new marketplaces.
- Cons: collectors must maintain a consistent contract for normalization and validation.
