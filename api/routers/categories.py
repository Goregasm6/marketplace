from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from core.plugins import PluginRegistry
from api.deps import get_plugin_registry

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("/", response_model=List[dict])
def list_categories(
    registry: PluginRegistry = Depends(get_plugin_registry),
) -> Any:
    """Retrieve all available categories."""
    categories = registry.get_categories()
    return [c.metadata for c in categories]

@router.get("/{name}", response_model=dict)
def get_category(
    name: str,
    registry: PluginRegistry = Depends(get_plugin_registry),
) -> Any:
    """Get category metadata by name."""
    category = registry.get(name)
    if not category or category.plugin_type != "category":
        raise HTTPException(status_code=404, detail="Category not found")
    return category.metadata
