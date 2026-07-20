from __future__ import annotations

import json
import re
from typing import Optional, Type, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T", bound=BaseModel)


class RiskAnalysisResponse(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    explanation: str
    risk_factors: list[str] = Field(default_factory=list)


class RepairEstimateResponse(BaseModel):
    needed: bool
    difficulty: str  # easy, medium, hard, unknown
    estimated_cost: Optional[float] = None
    notes: str


class SellerMotivationResponse(BaseModel):
    urgency: str  # low, medium, high
    motivation_type: str  # e.g., moving, upgrading, business
    negotiable: Optional[bool] = None
    summary: str


class OpportunityAnalysisResponse(BaseModel):
    has_misspellings: bool
    is_wrong_category: bool
    missing_model_number: bool
    is_bundle: bool
    poor_photos: bool
    explanation: str
    detected_factors: list[str] = Field(default_factory=list)


class ResponseParser:
    """Parses AI responses into structured data."""

    @staticmethod
    def extract_json(text: str) -> str:
        """Extract JSON block from markdown-formatted text."""
        # Try to find JSON block
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # If no block, try to find first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start : end + 1]

        return text.strip()

    def parse_as(self, text: str, model_class: Type[T]) -> T:
        """Parse text as a Pydantic model."""
        json_str = self.extract_json(text)
        try:
            data = json.loads(json_str)
            return model_class.model_validate(data)
        except (json.JSONDecodeError, Exception) as e:
            # Fallback or re-raise
            raise ValueError(f"Failed to parse response as {model_class.__name__}: {e}")

    def parse_list(self, text: str) -> list[str]:
        """Parse text as a list of strings (e.g., labels)."""
        # Common formats: comma separated, or bullet points
        if "," in text and "\n" not in text:
            return [i.strip() for i in text.split(",") if i.strip()]

        lines = text.splitlines()
        results = []
        for line in lines:
            # Remove bullet points like "- item" or "1. item"
            cleaned = re.sub(r"^[\s\d\.\-\*]+", "", line).strip()
            if cleaned:
                results.append(cleaned)
        return results
