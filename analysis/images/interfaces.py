from __future__ import annotations

from typing import Protocol, runtime_checkable

from analysis.images.types import ImageDetection


@runtime_checkable
class ImageOCR(Protocol):
    """Interface for Optical Character Recognition."""

    def extract_text(self, image_url: str) -> str:
        """Extract text from an image."""
        ...


@runtime_checkable
class ObjectDetector(Protocol):
    """Interface for detecting objects within an image."""

    def detect_objects(self, image_url: str) -> list[ImageDetection]:
        """Identify and locate objects in an image."""
        ...


@runtime_checkable
class ImageClassifier(Protocol):
    """Interface for classifying the whole image."""

    def classify(self, image_url: str) -> list[ImageDetection]:
        """Categorize an image into labels."""
        ...


@runtime_checkable
class BrandRecognizer(Protocol):
    """Interface for identifying brands in an image."""

    def identify_brands(self, image_url: str) -> list[str]:
        """Identify brands from logos or text in an image."""
        ...


@runtime_checkable
class ModelNumberRecognizer(Protocol):
    """Interface for identifying specific model numbers."""

    def identify_models(self, image_url: str) -> list[str]:
        """Extract model numbers from labels or packaging in an image."""
        ...


@runtime_checkable
class DuplicateDetector(Protocol):
    """Interface for detecting if an image is a duplicate."""

    def check_duplicate(self, image_url: str, reference_urls: list[str]) -> bool:
        """Determine if an image is a duplicate of existing ones."""
        ...


@runtime_checkable
class DamageDetector(Protocol):
    """Interface for detecting damage on items."""

    def detect_damage(self, image_url: str) -> tuple[bool, str | None]:
        """Assess an item for visible damage, returns (is_damaged, description)."""
        ...
