# ADR 0002: Use SQLite first

- Status: Accepted
- Date: 2026-07-13

## Context
The initial system is a local-first tool for collecting and analyzing listings. It should work with minimal setup, run well in tests, and avoid operational overhead.

## Decision
Use SQLite as the default database backend for the first implementation, with configuration support for overriding the database path.

## Consequences
- Pros: zero-setup development, simple deployment, and excellent fit for a small-scale data pipeline.
- Cons: SQLite is not the best choice for high-concurrency or multi-node production workloads.
