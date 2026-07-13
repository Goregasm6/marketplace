from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine

from database.models import (
    Image,
    Listing,
    Opportunity,
    PriceHistory,
    Purchase,
    Search,
    Seller,
)


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_listing_creation_with_related_models(session: Session) -> None:
    seller = Seller(name="Example Seller", username="seller1", rating=4.8)
    search = Search(query="nintendo switch", source="craigslist")
    listing = Listing(
        title="Nintendo Switch OLED",
        description="Great condition",
        price=299.99,
        source="craigslist",
        external_id="listing-001",
        seller=seller,
        search=search,
    )

    listing.images.append(Image(url="https://example.com/1.jpg", caption="Front view"))
    listing.price_history.append(PriceHistory(price=279.99))
    listing.opportunities.append(
        Opportunity(
            potential_profit=30.0,
            confidence_score=0.87,
            notes="Strong margin",
        )
    )
    listing.purchase = Purchase(price_paid=299.99, notes="Purchased")

    session.add(seller)
    session.add(search)
    session.add(listing)
    session.commit()
    session.refresh(listing)

    assert listing.id is not None
    assert listing.created_at is not None
    assert listing.updated_at is not None
    assert listing.seller is seller
    assert listing.search is search
    assert len(listing.images) == 1
    assert len(listing.price_history) == 1
    assert len(listing.opportunities) == 1
    assert listing.purchase is not None


def test_relationships_round_trip_from_database(session: Session) -> None:
    seller = Seller(name="Round Trip Seller", username="seller2", rating=4.6)
    search = Search(query="iphone 15", source="ebay")
    listing = Listing(
        title="iPhone 15",
        description="Unlocked",
        price=749.0,
        source="ebay",
        external_id="listing-002",
        seller=seller,
        search=search,
    )
    listing.images.append(Image(url="https://example.com/2.jpg"))

    session.add(seller)
    session.add(search)
    session.add(listing)
    session.commit()
    session.refresh(listing)

    reloaded = session.get(Listing, listing.id)
    assert reloaded is not None
    assert reloaded.seller is not None
    assert reloaded.seller.name == "Round Trip Seller"
    assert reloaded.search is not None
    assert reloaded.search.query == "iphone 15"
    assert len(reloaded.images) == 1
    assert reloaded.images[0].url == "https://example.com/2.jpg"
