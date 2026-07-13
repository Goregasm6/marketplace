import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB = BASE_DIR / "database" / "listings.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def connect():
    return sqlite3.connect(DB)


def initialize():

    conn = connect()

    with SCHEMA_PATH.open() as f:
        conn.executescript(f.read())

    conn.close()


def add_listing(listing):

    conn = connect()

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO listings
    (
    source,
    title,
    description,
    price,
    url,
    location
    )
    VALUES (?, ?, ?, ?, ?, ?)

    """,
    (
    listing["source"],
    listing["title"],
    listing["description"],
    listing["price"],
    listing["url"],
    listing["location"]
    ))

    conn.commit()
    conn.close()