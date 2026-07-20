from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from sqlmodel import Session

from database.database import get_session
from database.repositories import (
    ListingRepository,
    OpportunityRepository,
    QueueRepository,
    SearchRepository,
    SellerRepository,
    PurchaseRepository,
)

from core.plugins import PluginRegistry, PluginLoader, get_default_registry

from core.scheduler import SchedulerService
from config.settings import settings

_scheduler_service = SchedulerService(settings=settings)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(
    request: Request,
    api_key_header: str = Depends(API_KEY_HEADER),
) -> str:
    """Validate the API key from the header."""
    # Whitelist public endpoints
    if request.url.path in ["/", "/docs", "/redoc", "/openapi.json"]:
        return ""

    if not settings.api_key:
        # If no API key is configured, allow access (for development)
        return ""

    if api_key_header == settings.api_key:
        return api_key_header

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate API key",
    )


async def get_current_user(
    api_key: str = Depends(get_api_key),
) -> Optional[dict]:
    """
    Dependency to get the current user.
    Currently uses API Key, but designed to be easily swapped for JWT.
    """
    # This is a placeholder for future JWT authentication.
    # When implementing JWT, this dependency would validate the token
    # and return the user object/claims.
    return {"id": "default_user", "api_key": api_key}


async def rate_limiter(
    request: Request,
    user: Optional[dict] = Depends(get_current_user),
) -> None:
    """
    Rate limiting hook (design only).
    This could be implemented using Redis or another in-memory store.
    """
    # Placeholder for rate limiting logic.
    # Example: check settings.rate_limit_requests_per_minute
    pass


def get_db() -> Generator[Session, None, None]:
    with get_session() as session:
        yield session


def get_plugin_registry() -> PluginRegistry:
    registry = get_default_registry()
    if not registry.all():
        loader = PluginLoader(registry)
        loader.discover()
    return registry


def get_scheduler_service() -> SchedulerService:
    return _scheduler_service


def get_listing_repository(session: Session = Depends(get_db)) -> ListingRepository:
    return ListingRepository(session=session)


def get_opportunity_repository(
    session: Session = Depends(get_db),
) -> OpportunityRepository:
    return OpportunityRepository(session=session)


def get_queue_repository(session: Session = Depends(get_db)) -> QueueRepository:
    return QueueRepository(session=session)


def get_search_repository(session: Session = Depends(get_db)) -> SearchRepository:
    return SearchRepository(session=session)


def get_seller_repository(session: Session = Depends(get_db)) -> SellerRepository:
    return SellerRepository(session=session)


def get_purchase_repository(session: Session = Depends(get_db)) -> PurchaseRepository:
    return PurchaseRepository(session=session)
