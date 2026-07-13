from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship, SQLModel


class ListingStatus(str, Enum):
    NEW = "new"
    WATCHING = "watching"
    WON = "won"
    PURCHASED = "purchased"
    ARCHIVED = "archived"


class BaseTimestampModel(SQLModel):
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={"server_default": "CURRENT_TIMESTAMP"},
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={"server_default": "CURRENT_TIMESTAMP"},
    )


class Seller(BaseTimestampModel, table=True):
    __tablename__ = "sellers"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True, min_length=1)
    username: Optional[str] = Field(default=None, index=True)
    rating: Optional[float] = Field(default=None)
    external_id: Optional[str] = Field(default=None, index=True)
    listings: Mapped[list["Listing"]] = Relationship(back_populates="seller")


class Search(BaseTimestampModel, table=True):
    __tablename__ = "searches"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    query: str = Field(index=True, min_length=1)
    source: str = Field(index=True, min_length=1)
    location: Optional[str] = Field(default=None, index=True)
    listings: Mapped[list["Listing"]] = Relationship(back_populates="search")


class Listing(BaseTimestampModel, table=True):
    __tablename__ = "listings"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(index=True, min_length=1)
    description: Optional[str] = Field(default=None)
    price: float = Field(ge=0)
    source: str = Field(index=True, min_length=1)
    external_id: Optional[str] = Field(default=None, unique=True, index=True)
    url: Optional[str] = Field(default=None)
    status: ListingStatus = Field(default=ListingStatus.NEW, index=True)
    seller_id: Optional[UUID] = Field(default=None, foreign_key="sellers.id")
    search_id: Optional[UUID] = Field(default=None, foreign_key="searches.id")

    seller: Optional[Seller] = Relationship(back_populates="listings")
    search: Optional[Search] = Relationship(back_populates="listings")
    images: Mapped[list["Image"]] = Relationship(back_populates="listing")
    price_history: Mapped[list["PriceHistory"]] = Relationship(back_populates="listing")
    opportunities: Mapped[list["Opportunity"]] = Relationship(back_populates="listing")
    purchase: Optional["Purchase"] = Relationship(back_populates="listing")


class Image(BaseTimestampModel, table=True):
    __tablename__ = "images"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    url: str = Field(index=True, min_length=1)
    caption: Optional[str] = Field(default=None)
    listing_id: Optional[UUID] = Field(default=None, foreign_key="listings.id", index=True)

    listing: Optional[Listing] = Relationship(back_populates="images")


class PriceHistory(BaseTimestampModel, table=True):
    __tablename__ = "price_history"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    price: float = Field(ge=0)
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    listing_id: Optional[UUID] = Field(default=None, foreign_key="listings.id", index=True)

    listing: Optional[Listing] = Relationship(back_populates="price_history")


class Opportunity(BaseTimestampModel, table=True):
    __tablename__ = "opportunities"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    potential_profit: float = Field(ge=0)
    confidence_score: float = Field(ge=0, le=1)
    notes: Optional[str] = Field(default=None)
    listing_id: Optional[UUID] = Field(default=None, foreign_key="listings.id", index=True)

    listing: Optional[Listing] = Relationship(back_populates="opportunities")


class Purchase(BaseTimestampModel, table=True):
    __tablename__ = "purchases"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    price_paid: float = Field(ge=0)
    purchased_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    notes: Optional[str] = Field(default=None)
    listing_id: Optional[UUID] = Field(default=None, foreign_key="listings.id", unique=True, index=True)

    listing: Optional[Listing] = Relationship(back_populates="purchase")
