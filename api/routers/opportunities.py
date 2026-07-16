from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from database.repositories import OpportunityRepository
from database.schemas import OpportunityCreate, OpportunityRead
from api.deps import get_opportunity_repository

router = APIRouter(prefix="/opportunities", tags=["opportunities"])

@router.get("/", response_model=List[OpportunityRead])
def list_opportunities(
    repo: OpportunityRepository = Depends(get_opportunity_repository),
) -> Any:
    """Retrieve all opportunities."""
    return repo.list()

@router.get("/{opportunity_id}", response_model=OpportunityRead)
def get_opportunity(
    opportunity_id: UUID,
    repo: OpportunityRepository = Depends(get_opportunity_repository),
) -> Any:
    """Get a single opportunity by ID."""
    opportunity = repo.get_by_id(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity

@router.post("/", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    opportunity_in: OpportunityCreate,
    repo: OpportunityRepository = Depends(get_opportunity_repository),
) -> Any:
    """Create a new opportunity."""
    from database.models import Opportunity
    opportunity = Opportunity(**opportunity_in.model_dump())
    return repo.create(opportunity)

@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_opportunity(
    opportunity_id: UUID,
    repo: OpportunityRepository = Depends(get_opportunity_repository),
) -> None:
    """Delete an opportunity."""
    repo.delete(opportunity_id)
