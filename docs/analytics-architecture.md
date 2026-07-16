# Analytics architecture

SQLite remains MAIE's operational database. Collectors, repositories, and
application workflows read and write only SQLite. DuckDB is a separate
analytics snapshot used only for reporting.

```
collectors / repositories / application
                 | read-write
              SQLite
                 | read-only sync
              DuckDB warehouse
                 | read-only queries
          analytics dashboard / reports
```

`analytics.warehouse.sync_operational_data()` opens SQLite with `mode=ro`,
copies its current tables into `analytics/warehouse.duckdb`, and creates the
`listing_facts` reporting view. The sync performs no SQLite writes and does
not import repositories or operational models.

DuckDB connections returned for reports are read-only. Refreshing the snapshot
is the only analytics write operation, and it writes only the DuckDB file. A
scheduled job can call the sync after operational collection completes; it is
not part of the collector or repository transaction path.

The reporting view exposes persisted category, FlipScore, and keyword-score
fields when the operational schema contains them. Analytics intentionally does
not recompute those values, so scoring and categorization remain owned by the
operational application. With the current schema, category and FlipScore
metrics are empty until those values are persisted by the operational workflow.

## Usage

```python
from analytics.dashboard import dashboard_data
from analytics.warehouse import sync_operational_data

sync_operational_data()
report = dashboard_data()
```

The available query functions cover profitable categories, average FlipScore,
median asking prices, price reductions, seller frequency, search-keyword
performance, category trends, and daily listing volume.
