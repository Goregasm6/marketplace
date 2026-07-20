from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database.repositories import QueueRepository
from database.schemas import QueueRead
from database.models import QueueStatus
from api.deps import get_queue_repository

router = APIRouter(prefix="/queue", tags=["queue"])


class QueueActionRequest(BaseModel):
    notes: Optional[str] = None


@router.get("/", response_model=List[QueueRead])
def list_queue(
    status: QueueStatus = None,
    repo: QueueRepository = Depends(get_queue_repository),
) -> Any:
    """Retrieve all items in the review queue, optionally filtered by status."""
    if status:
        return repo.list_by_status(status)
    return repo.list()


@router.get("/{queue_id}", response_model=QueueRead)
def get_queue_item(
    queue_id: UUID,
    repo: QueueRepository = Depends(get_queue_repository),
) -> Any:
    """Get a single queue item by ID."""
    item = repo.get_by_id(queue_id)
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return item


@router.post("/{queue_id}/review", response_model=QueueRead)
def review_queue_item(
    queue_id: UUID,
    request: QueueActionRequest,
    repo: QueueRepository = Depends(get_queue_repository),
) -> Any:
    """Mark a queue item as being reviewed."""
    item = repo.review(queue_id, request.notes)
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return item


@router.post("/{queue_id}/approve", response_model=QueueRead)
def approve_queue_item(
    queue_id: UUID,
    request: QueueActionRequest,
    repo: QueueRepository = Depends(get_queue_repository),
) -> Any:
    """Approve an opportunity in the queue."""
    item = repo.approve(queue_id, request.notes)
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return item


@router.post("/{queue_id}/reject", response_model=QueueRead)
def reject_queue_item(
    queue_id: UUID,
    request: QueueActionRequest,
    repo: QueueRepository = Depends(get_queue_repository),
) -> Any:
    """Reject an opportunity in the queue."""
    item = repo.reject(queue_id, request.notes)
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return item


@router.post("/{queue_id}/archive", response_model=QueueRead)
def archive_queue_item(
    queue_id: UUID,
    request: QueueActionRequest,
    repo: QueueRepository = Depends(get_queue_repository),
) -> Any:
    """Archive a queue item."""
    item = repo.archive(queue_id, request.notes)
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return item
