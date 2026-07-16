from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from core.plugins import PluginRegistry
from api.deps import get_plugin_registry

router = APIRouter(prefix="/collectors", tags=["collectors"])

@router.get("/", response_model=List[dict])
def list_collectors(
    registry: PluginRegistry = Depends(get_plugin_registry),
) -> Any:
    """Retrieve all available collectors."""
    collectors = registry.get_collectors()
    return [c.metadata for c in collectors]

@router.get("/{name}", response_model=dict)
def get_collector(
    name: str,
    registry: PluginRegistry = Depends(get_plugin_registry),
) -> Any:
    """Get collector metadata by name."""
    collector = registry.get(name)
    if not collector or collector.plugin_type != "collector":
        raise HTTPException(status_code=404, detail="Collector not found")
    return collector.metadata
