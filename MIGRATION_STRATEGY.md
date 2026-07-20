# Migration Strategy: SQLite to PostgreSQL

This document outlines the strategy for migrating the MAIE operational database from SQLite to PostgreSQL.

## 1. Abstraction Layer (Completed)
The codebase has been refactored to support multiple database backends:
- **`database_url` in Settings**: Allows specifying a PostgreSQL connection string (`postgresql://user:password@host:port/dbname`).
- **Dialect-Agnostic Repositories**: `DatabaseRepository` handles basic CRUD operations without dialect-specific SQL.
- **Strategy Pattern for Initialization**: SQLite-specific triggers are isolated in `SQLiteInitializer`. A `PostgresInitializer` placeholder is ready for PostgreSQL-specific setup (e.g., PL/pgSQL triggers).
- **Optimistic Locking**: Added `version` column and `version_id_col` mapper arguments to support concurrent workers and prevent lost updates.

## 2. Migration Tooling
We recommend using **Alembic** for managing schema migrations.
- **Setup**: `uv add alembic`
- **Initialization**: `alembic init migrations`
- **Configuration**: Update `alembic.ini` and `env.py` to use the `SQLModel` metadata and the `DATABASE_URL` from the application settings.

## 3. Data Migration Steps
When moving existing data from `listings.db` to a PostgreSQL instance:
1. **Schema Creation**: Use Alembic to create the schema in the target PostgreSQL database.
2. **Data Export**: Export SQLite data to CSV or JSON, or use a tool like `pgloader`.
3. **Data Type Mapping**: 
   - SQLite `TEXT` -> PostgreSQL `TEXT` or `VARCHAR`.
   - SQLite `BLOB` -> PostgreSQL `BYTEA`.
   - SQLite `UUID` (stored as string) -> PostgreSQL `UUID` (native).
4. **Trigger Implementation**: Implement the PostgreSQL version of the `after_delete` triggers using PL/pgSQL functions.

## 4. Concurrent Workers Support
PostgreSQL's MVCC and the newly added optimistic locking support high concurrency.
- **Connection Pooling**: SQLAlchemy's `QueuePool` (default for PostgreSQL) should be tuned based on the number of workers.
- **Transaction Isolation**: Default `READ COMMITTED` is usually sufficient, but can be adjusted if needed.

## 5. Deployment
1. Set the `DATABASE_URL` environment variable to point to the PostgreSQL instance.
2. Run `alembic upgrade head` to ensure the schema is up to date.
3. The application will automatically use the `PostgresInitializer` (if implemented) and standard SQLAlchemy PostgreSQL dialect.
