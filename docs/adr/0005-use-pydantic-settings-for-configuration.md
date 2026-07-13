# ADR 0005: Use Pydantic Settings for configuration

- Status: Accepted
- Date: 2026-07-13

## Context
Application settings need validation, clear defaults, and support for environment variables and local configuration files. A lightweight configuration approach is preferable to ad hoc globals.

## Decision
Use Pydantic Settings for application configuration so settings are validated at startup and documented in one place.

## Consequences
- Pros: explicit validation, better error messages, and a simple way to manage runtime options.
- Cons: configuration becomes slightly more structured than a minimal dictionary-based approach.
