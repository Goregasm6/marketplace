from pathlib import Path
from typing import Optional

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.config import DATABASE
from database.models import Listing, Queue  # noqa: F401


BASE_DIR = Path(__file__).resolve().parent.parent
DB = BASE_DIR / "database" / "listings.db"


def get_engine(database_url: Optional[str] = None) -> Engine:
    target = database_url or DATABASE or str(DB)
    if target.startswith("sqlite"):
        return create_engine(target)
    return create_engine(f"sqlite:///{target}")


def get_session(database_url: Optional[str] = None, *, expire_on_commit: bool = False) -> Session:
    return Session(get_engine(database_url), expire_on_commit=expire_on_commit)


def connect(database_url: Optional[str] = None) -> Session:
    return get_session(database_url)


def initialize_database(database_url: Optional[str] = None) -> Engine:
    engine = get_engine(database_url)
    SQLModel.metadata.create_all(engine)
    return engine


def initialize() -> Engine:
    return initialize_database()


def add_listing(listing: dict) -> None:
    with connect() as session:
        entry = Listing(
            title=listing["title"],
            description=listing.get("description"),
            price=float(listing["price"]),
            source=listing["source"],
            external_id=listing.get("url"),
            url=listing.get("url"),
        )
        session.add(entry)
        session.commit()
