# Analytics Synchronization Strategy

MAIE uses an incremental synchronization process to keep the DuckDB analytics warehouse up-to-date with the operational SQLite database. This replaces the previous "drop and reload" strategy with a more efficient, scalable approach.

## Components

### 1. ChangeTracker
Identifies records that have been created, modified, or deleted in the operational database since the last synchronization.
- **Updates/Inserts**: Detected using the `updated_at` timestamp on each table.
- **Deletions**: Detected using a `deleted_records` audit table in SQLite, populated via database triggers.

### 2. BatchProcessor
Handles the application of changes to DuckDB in configurable batch sizes.
- **Upserts**: Implemented as a "Delete by ID + Insert" transaction to ensure idempotency without relying on complex `ON CONFLICT` logic across all DuckDB versions.
- **Deletes**: Performed in batches for efficiency.

### 3. SyncManager
Orchestrates the entire process:
1. Retrieves the `last_sync_at` timestamp for each table from DuckDB's `sync_metadata` table.
2. Fetches changes from SQLite.
3. Applies changes to DuckDB using the `BatchProcessor`.
4. Updates the `sync_metadata` with the new timestamp upon successful completion.

### 4. Metrics
Collects detailed statistics for each synchronization session, including:
- Rows inserted/updated.
- Rows deleted.
- Duration of the sync.
- Errors encountered.

## Design Goals

### Scalability
By processing only changed records and using batch operations, the system can handle millions of listings without reloading the entire dataset.

### Robustness & Resumability
The synchronization is wrapped in DuckDB transactions. If a sync fails, the `sync_metadata` is not updated, allowing the next run to resume from the last successful point.

### Data Consistency
The use of `updated_at` ensures that all intermediate state changes are eventually captured. Deletes are tracked explicitly to ensure the warehouse does not contain orphaned records.

## Usage

Synchronization is triggered via the `Warehouse.sync()` method:

```python
from analytics.warehouse import Warehouse

warehouse = Warehouse()
metrics = warehouse.sync()
print(f"Synced {metrics.tables_synced['listings'].inserted_or_updated} listings.")
```
