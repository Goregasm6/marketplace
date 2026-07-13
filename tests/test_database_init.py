from __future__ import annotations

from pathlib import Path

from database.database import initialize_database


def test_initialize_database_creates_expected_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "maie-test.db"

    engine = initialize_database(str(db_path))

    with engine.begin() as conn:
        tables = conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

    table_names = {name for (name,) in tables}
    assert "listings" in table_names
    assert "sellers" in table_names
    assert "searches" in table_names
