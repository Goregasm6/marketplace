from __future__ import annotations

import pytest
from sqlalchemy.orm.exc import StaleDataError
from database.database import initialize_database, SQLiteInitializer, PostgresInitializer
from database.models import Seller
from database.repositories import SellerRepository

def test_optimistic_locking(tmp_path):
    """Verify that optimistic locking works using the version column."""
    db_url = f"sqlite:///{tmp_path / 'test_locking.db'}"
    initialize_database(db_url)
    
    repo = SellerRepository(database_url=db_url)
    seller = repo.create(Seller(name="Original Name"))
    
    # Fetch two instances of the same record
    s1 = repo.get_by_id(seller.id)
    s2 = repo.get_by_id(seller.id)
    
    assert s1.version == 1
    assert s2.version == 1
    
    # Update the first instance
    repo.update(s1.id, {"name": "First Update"})
    
    # Verify version incremented
    updated_s1 = repo.get_by_id(seller.id)
    assert updated_s1.version == 2
    
    # Attempt to update the second (stale) instance
    with pytest.raises(StaleDataError):
        # We need to use the stale object directly in a way that triggers the check.
        # The repository's update method currently fetches the latest instance by ID.
        # To test optimistic locking, we need to try to save an object with an old version.
        with repo.session() as session:
            s2.name = "Stale Update"
            session.add(s2)
            # This should raise StaleDataError on commit/flush because version is still 1
            session.flush()

def test_dialect_detection(tmp_path):
    """Verify that the correct initializer is chosen based on the URL."""
    sqlite_url = f"sqlite:///{tmp_path / 'test.db'}"
    postgres_url = "postgresql://user:pass@localhost/db"
    
    # We can't easily test initialize_database with a fake postgres URL without a driver,
    # but we can test the logic if we mock the engine creation or just check the URL.
    from database.database import get_engine
    
    engine_sqlite = get_engine(sqlite_url)
    assert engine_sqlite.dialect.name == "sqlite"
    
    # For postgres, we'd need psycopg2 or similar installed to even create the engine
    # but we can check our initialization logic.
    
    from unittest.mock import MagicMock, patch
    
    with patch("database.database.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        with patch.object(SQLiteInitializer, "initialize") as mock_sqlite_init:
            initialize_database(sqlite_url)
            mock_sqlite_init.assert_called_once()
            
        with patch.object(PostgresInitializer, "initialize") as mock_pg_init:
            initialize_database(postgres_url)
            mock_pg_init.assert_called_once()
