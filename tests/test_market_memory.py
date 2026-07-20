from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from analysis.market_memory import (
    ListingHistoryService,
    PriceHistoryService,
    SellerHistoryService,
)
from database.database import get_session, initialize_database
from database.models import Listing, ListingStatus, Seller


def _listing(title: str, price: float, external_id: str, **values: object) -> Listing:
    return Listing(
        title=title, price=price, source="market", external_id=external_id, **values
    )


def test_price_history_records_every_observation_and_detects_drops(tmp_path) -> None:
    db_path = tmp_path / "memory.db"
    initialize_database(str(db_path))
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service = ListingHistoryService(str(db_path))

    listing = _listing("Canon EOS R5", 3000, "r5-1", created_at=start)
    result = service.observe(listing, start)
    service.observe(_listing("Canon EOS R5", 3000, "r5-1"), start + timedelta(days=1))
    service.observe(_listing("Canon EOS R5", 2700, "r5-1"), start + timedelta(days=3))

    metrics = PriceHistoryService(str(db_path)).metrics(result.listing.id)  # type: ignore[arg-type]
    assert metrics.observation_count == 3
    assert metrics.has_price_changed
    assert metrics.change_count == 1
    assert metrics.price_drop_count == 1
    assert metrics.initial_price == 3000
    assert metrics.current_price == 2700
    assert metrics.lowest_price == 2700


def test_listing_memory_identifies_seen_relists_keywords_and_similar_sale_time(
    tmp_path,
) -> None:
    db_path = tmp_path / "listing-memory.db"
    initialize_database(str(db_path))
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service = ListingHistoryService(str(db_path))

    original = service.observe(
        _listing("Vintage Nikon F3 Camera", 500, "nikon-old", created_at=start), start
    )
    relist = _listing(
        "Vintage Nikon F3 Camera",
        450,
        "nikon-new",
        created_at=start + timedelta(days=10),
    )
    assert service.has_seen_before(relist)
    new_result = service.observe(relist, start + timedelta(days=10))
    assert new_result.is_new_listing
    assert new_result.relisted_from_id == original.listing.id

    sold = _listing(
        "Vintage Nikon F3 Camera",
        550,
        "nikon-sold",
        status=ListingStatus.ARCHIVED,
        created_at=start - timedelta(days=8),
        updated_at=start,
    )
    service.observe(sold, start)

    metrics = service.metrics(new_result.listing.id, as_of=start + timedelta(days=12))  # type: ignore[arg-type]
    assert metrics.has_seen_before is False  # one observation for this new relist
    assert metrics.days_on_market == 0
    assert original.listing.id in metrics.relisted_from_ids
    assert {"vintage", "nikon", "camera"} <= set(metrics.repeated_keywords)
    assert metrics.similar_listings_average_days_to_sell == pytest.approx(8.0)


def test_seller_history_flags_repeated_underpricing(tmp_path) -> None:
    db_path = tmp_path / "seller-memory.db"
    initialize_database(str(db_path))
    seller_service = SellerHistoryService(str(db_path), underprice_ratio=0.85)
    listing_service = ListingHistoryService(str(db_path))
    with get_session(str(db_path)) as session:
        seller = Seller(name="Fast Deals")
        session.add(seller)
        session.commit()
        session.refresh(seller)
        seller_id = seller.id

    for index in range(3):
        listing_service.observe(
            _listing("Sony A7 IV Body", 700, f"seller-{index}", seller_id=seller_id)
        )
        listing_service.observe(_listing("Sony A7 IV Body", 1200, f"market-{index}"))

    metrics = seller_service.metrics(seller_id)  # type: ignore[arg-type]
    assert metrics.listing_count == 3
    assert metrics.comparable_listing_count == 3
    assert metrics.underpriced_listing_count == 3
    assert metrics.underpricing_rate == 1.0
    assert metrics.is_frequently_underpricing


def test_unknown_listing_price_history_is_rejected(tmp_path) -> None:
    db_path = tmp_path / "unknown-listing.db"
    initialize_database(str(db_path))

    with pytest.raises(LookupError):
        PriceHistoryService(str(db_path)).metrics(__import__("uuid").uuid4())
