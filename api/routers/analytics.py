from typing import Any, List

from fastapi import APIRouter
from analytics import queries

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/most-profitable-categories", response_model=List[dict])
def get_most_profitable_categories() -> Any:
    return queries.most_profitable_categories()

@router.get("/average-flipscore", response_model=List[dict])
def get_average_flipscore() -> Any:
    return queries.average_flipscore()

@router.get("/median-asking-prices", response_model=List[dict])
def get_median_asking_prices() -> Any:
    return queries.median_asking_prices()

@router.get("/price-reductions", response_model=List[dict])
def get_price_reductions() -> Any:
    return queries.price_reductions()

@router.get("/seller-frequency", response_model=List[dict])
def get_seller_frequency() -> Any:
    return queries.seller_frequency()

@router.get("/keyword-performance", response_model=List[dict])
def get_keyword_performance() -> Any:
    return queries.keyword_performance()

@router.get("/category-trends", response_model=List[dict])
def get_category_trends() -> Any:
    return queries.category_trends()

@router.get("/daily-listing-volume", response_model=List[dict])
def get_daily_listing_volume() -> Any:
    return queries.daily_listing_volume()
