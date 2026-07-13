from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from database.models import ListingStatus


class SellerBase(BaseModel):
    name: str
    username: Optional[str] = None
    rating: Optional[float] = None
    external_id: Optional[str] = None


class SellerCreate(SellerBase):
    pass


class SellerRead(SellerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SearchBase(BaseModel):
    query: str
    source: str
    location: Optional[str] = None


class SearchCreate(SearchBase):
    pass


class SearchRead(SearchBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListingBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    source: str
    external_id: Optional[str] = None
    url: Optional[str] = None
    status: ListingStatus = ListingStatus.NEW


class ListingCreate(ListingBase):
    seller_id: Optional[UUID] = None
    search_id: Optional[UUID] = None


class ListingRead(ListingBase):
    id: UUID
    seller_id: Optional[UUID] = None
    search_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImageBase(BaseModel):
    url: str
    caption: Optional[str] = None


class ImageCreate(ImageBase):
    listing_id: Optional[UUID] = None


class ImageRead(ImageBase):
    id: UUID
    listing_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceHistoryBase(BaseModel):
    price: float


class PriceHistoryCreate(PriceHistoryBase):
    listing_id: Optional[UUID] = None


class PriceHistoryRead(PriceHistoryBase):
    id: UUID
    listing_id: Optional[UUID] = None
    observed_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OpportunityBase(BaseModel):
    potential_profit: float
    confidence_score: float
    notes: Optional[str] = None


class OpportunityCreate(OpportunityBase):
    listing_id: Optional[UUID] = None


class OpportunityRead(OpportunityBase):
    id: UUID
    listing_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseBase(BaseModel):
    price_paid: float
    notes: Optional[str] = None


class PurchaseCreate(PurchaseBase):
    listing_id: Optional[UUID] = None


class PurchaseRead(PurchaseBase):
    id: UUID
    listing_id: Optional[UUID] = None
    purchased_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
