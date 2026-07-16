"""Read-only analytical reporting over a DuckDB warehouse snapshot.

This package never writes to the operational SQLite database.  Use
``sync_operational_data`` to refresh its DuckDB snapshot, then use the query
and dashboard helpers to read aggregate results.
"""

from analytics.warehouse import SyncResult, Warehouse, sync_operational_data

__all__ = ["SyncResult", "Warehouse", "sync_operational_data"]
