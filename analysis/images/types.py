from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BoundingBox:
    """Coordinates for an object in an image."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float | None = None


@dataclass
class ImageDetection:
    """A detected object or feature in an image."""

    label: str
    confidence: float
    box: BoundingBox | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageAnalysisResult:
    """Consolidated result of image analysis for a single image."""

    image_url: str
    ocr_text: str | None = None
    objects: list[ImageDetection] = field(default_factory=list)
    labels: list[ImageDetection] = field(default_factory=list)
    brands: list[str] = field(default_factory=list)
    model_numbers: list[str] = field(default_factory=list)
    is_duplicate: bool = False
    damage_detected: bool = False
    damage_details: str | None = None
    raw_results: dict[str, Any] = field(default_factory=dict)
