from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from core.scheduler import SchedulerService
from api.deps import get_scheduler_service

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

@router.get("/status", response_model=dict)
def get_scheduler_status(
    service: SchedulerService = Depends(get_scheduler_service),
) -> Any:
    """Show scheduler configuration and recent execution metrics."""
    return service.status()

@router.post("/start", response_model=dict)
def start_scheduler(
    service: SchedulerService = Depends(get_scheduler_service),
) -> Any:
    """Start the background scheduler."""
    service.start()
    return {"message": "Scheduler started"}

@router.post("/stop", response_model=dict)
def stop_scheduler(
    service: SchedulerService = Depends(get_scheduler_service),
) -> Any:
    """Stop the background scheduler."""
    service.shutdown()
    return {"message": "Scheduler stopped"}

@router.post("/run/{collector_name}", response_model=dict)
def run_collector(
    collector_name: str,
    service: SchedulerService = Depends(get_scheduler_service),
) -> Any:
    """Run a collector job immediately."""
    result = service.run_job(collector_name)
    if result.get("status") == "failed":
         raise HTTPException(status_code=500, detail=result.get("error"))
    return result
