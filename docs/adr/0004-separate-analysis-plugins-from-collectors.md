# ADR 0004: Keep analysis logic separate from collectors

- Status: Accepted
- Date: 2026-07-13

## Context
Scoring, enrichment, and future AI features should not be mixed into source-specific collector code. That would make collectors harder to test and harder to evolve.

## Decision
Keep collectors focused on fetching and normalization, and place scoring and analysis features in dedicated analysis plugins that operate on normalized listing data.

## Consequences
- Pros: cleaner boundaries, better reuse, and easier future integration of AI or predictive features.
- Cons: requires an explicit data contract between collectors and downstream analysis modules.
