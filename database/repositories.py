from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Callable, Generic, Optional, TypeVar
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, SQLModel, select

from database.database import get_session
from database.models import (
    Listing,
    ListingStatus,
    Opportunity,
    PriceHistory,
    Purchase,
    Search,
    Seller,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ModelType = TypeVar("ModelType", bound=SQLModel)


class DatabaseRepository(Generic[ModelType]):
    def __init__(
        self,
        model_type: type[ModelType],
        database_url: Optional[str] = None,
        *,
        session: Optional[Session] = None,
        session_factory: Optional[Callable[[], Session]] = None,
    ) -> None:
        self.model_type = model_type
        self.database_url = database_url
        self._session = session
        self._session_factory = session_factory or (lambda: get_session(database_url, expire_on_commit=False))

    @contextmanager
    def session(self) -> Session:
        if self._session is not None:
            yield self._session
            return

        managed_session = self._session_factory()
        try:
            yield managed_session
            managed_session.commit()
        except SQLAlchemyError as exc:
            managed_session.rollback()
            logger.exception("Database operation failed for %s", self.model_type.__name__)
            raise exc
        finally:
            managed_session.close()

    def create(self, instance: ModelType) -> ModelType:
        logger.info("Creating %s", self.model_type.__name__)
        with self.session() as session:
            session.add(instance)
            session.flush()
            session.refresh(instance)
            return instance

    def get_by_id(self, instance_id: UUID | str | None) -> Optional[ModelType]:
        if instance_id is None:
            return None
        with self.session() as session:
            return session.get(self.model_type, instance_id)

    def list(self) -> list[ModelType]:
        logger.info("Listing %s records", self.model_type.__name__)
        with self.session() as session:
            statement = select(self.model_type)
            return list(session.exec(statement).all())

    def update(self, instance_id: UUID | str | None, values: dict[str, Any]) -> Optional[ModelType]:
        if instance_id is None:
            return None
        logger.info("Updating %s %s", self.model_type.__name__, instance_id)
        with self.session() as session:
            instance = session.get(self.model_type, instance_id)
            if instance is None:
                return None
            for key, value in values.items():
                setattr(instance, key, value)
            session.add(instance)
            session.flush()
            session.refresh(instance)
            return instance

    def delete(self, instance_id: UUID | str | None) -> None:
        if instance_id is None:
            return None
        logger.info("Deleting %s %s", self.model_type.__name__, instance_id)
        with self.session() as session:
            instance = session.get(self.model_type, instance_id)
            if instance is None:
                return None
            session.delete(instance)
            session.flush()


class SellerRepository(DatabaseRepository[Seller]):
    def __init__(self, database_url: Optional[str] = None, *, session: Optional[Session] = None) -> None:
        super().__init__(Seller, database_url=database_url, session=session)


class SearchRepository(DatabaseRepository[Search]):
    def __init__(self, database_url: Optional[str] = None, *, session: Optional[Session] = None) -> None:
        super().__init__(Search, database_url=database_url, session=session)


class ListingRepository(DatabaseRepository[Listing]):
    def __init__(self, database_url: Optional[str] = None, *, session: Optional[Session] = None) -> None:
        super().__init__(Listing, database_url=database_url, session=session)

    def list_by_status(self, status: ListingStatus) -> list[Listing]:
        logger.info("Listing %s records for status %s", self.model_type.__name__, status)
        with self.session() as session:
            statement = select(Listing).where(Listing.status == status)
            return list(session.exec(statement).all())


class PriceHistoryRepository(DatabaseRepository[PriceHistory]):
    def __init__(self, database_url: Optional[str] = None, *, session: Optional[Session] = None) -> None:
        super().__init__(PriceHistory, database_url=database_url, session=session)

    def list_for_listing(self, listing_id: UUID | str | None) -> list[PriceHistory]:
        if listing_id is None:
            return []
        logger.info("Listing price history for listing %s", listing_id)
        with self.session() as session:
            statement = select(PriceHistory).where(PriceHistory.listing_id == listing_id)
            return list(session.exec(statement).all())


class OpportunityRepository(DatabaseRepository[Opportunity]):
    def __init__(self, database_url: Optional[str] = None, *, session: Optional[Session] = None) -> None:
        super().__init__(Opportunity, database_url=database_url, session=session)

    def list_for_listing(self, listing_id: UUID | str | None) -> list[Opportunity]:
        if listing_id is None:
            return []
        logger.info("Listing opportunities for listing %s", listing_id)
        with self.session() as session:
            statement = select(Opportunity).where(Opportunity.listing_id == listing_id)
            return list(session.exec(statement).all())


class PurchaseRepository(DatabaseRepository[Purchase]):
    def __init__(self, database_url: Optional[str] = None, *, session: Optional[Session] = None) -> None:
        super().__init__(Purchase, database_url=database_url, session=session)

    def get_by_listing_id(self, listing_id: UUID | str | None) -> Optional[Purchase]:
        if listing_id is None:
            return None
        logger.info("Fetching purchase for listing %s", listing_id)
        with self.session() as session:
            statement = select(Purchase).where(Purchase.listing_id == listing_id)
            return session.exec(statement).one_or_none()
