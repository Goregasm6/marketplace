# ADR 0001: Use SQLModel for persistence models

- Status: Accepted
- Date: 2026-07-13

## Context
The project needs typed database models, simple CRUD operations, and a lightweight Python-native persistence layer. We want to keep the codebase approachable while still supporting clear relationships between entities.

## Decision
Use SQLModel for persistence models, with repository code keeping database concerns separate from application logic.

## Consequences
- Pros: concise models, strong typing, and a straightforward path for local development and testing.
- Cons: advanced database features may require falling back to lower-level SQLAlchemy patterns in the future.
