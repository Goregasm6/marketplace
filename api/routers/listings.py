from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from database.repositories import ListingRepository
from database.schemas import ListingCreate, ListingRead, ListingUpdate
from database.models import ListingStatus
from api.deps import get_listing_repository

router = APIRouter(prefix="/listings", tags=["listings"])

@router.get("/", response_model=List[ListingRead])
def list_listings(
    status: ListingStatus = None,
    repo: ListingRepository = Depends(get_listing_repository),
) -> Any:
    """Retrieve all listings, optionally filtered by status."""
    if status:
        return repo.list_by_status(status)
    return repo.list()

@router.get("/{listing_id}", response_model=ListingRead)
def get_listing(
    listing_id: UUID,
    repo: ListingRepository = Depends(get_listing_repository),
) -> Any:
    """Get a single listing by ID."""
    listing = repo.get_by_id(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

@router.post("/", response_model=ListingRead, status_code=status.HTTP_201_CREATED)
def create_listing(
    listing_in: ListingCreate,
    repo: ListingRepository = Depends(get_listing_repository),
) -> Any:
    """Create a new listing."""
    from database.models import Listing
    listing = Listing(**listing_in.model_dump())
    return repo.create(listing)

@router.patch("/{listing_id}", response_model=ListingRead)
def update_listing(
    listing_id: UUID,
    listing_in: ListingUpdate,
    repo: ListingRepository = Depends(get_listing_repository),
) -> Any:
    """Update an existing listing."""
    listing = repo.update(listing_id, listing_in.model_dump(exclude_unset=True))
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: UUID,
    repo: ListingRepository = Depends(get_listing_repository),
) -> None:
    """Delete a listing."""
    repo.delete(listing_id)
