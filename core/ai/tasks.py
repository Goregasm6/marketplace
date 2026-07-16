from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.ai.parser import (
    OpportunityAnalysisResponse,
    RepairEstimateResponse,
    ResponseParser,
    RiskAnalysisResponse,
    SellerMotivationResponse,
)
from core.ai.prompt import PromptManager
from core.ai.router import TaskRouter


class AIService:
    """High-level service for executing AI tasks."""

    def __init__(self):
        self.router = TaskRouter()
        self.prompts = PromptManager()
        self.parser = ResponseParser()

    def normalize_title(self, title: str) -> str:
        prompt = self.prompts.get_prompt("title_normalization", title=title)
        return self.router.execute_task("title_normalization", prompt).strip()

    def cleanup_description(self, description: str) -> str:
        prompt = self.prompts.get_prompt("description_cleanup", description=description)
        return self.router.execute_task("description_cleanup", prompt).strip()

    def analyze_seller_motivation(self, title: str, description: str) -> SellerMotivationResponse:
        prompt = self.prompts.get_prompt("seller_motivation", title=title, description=description)
        # We ask for JSON in the prompt if we want structured data
        prompt += "\n\nReturn response as JSON with keys: urgency, motivation_type, negotiable (bool), summary."
        text = self.router.execute_task("seller_motivation", prompt)
        return self.parser.parse_as(text, SellerMotivationResponse)

    def classify_category(self, title: str, description: str, categories: List[str]) -> str:
        prompt = self.prompts.get_prompt(
            "category_classification",
            title=title,
            description=description,
            categories=", ".join(categories),
        )
        return self.router.execute_task("category_classification", prompt).strip()

    def estimate_repair(self, title: str, description: str) -> RepairEstimateResponse:
        prompt = self.prompts.get_prompt("repair_estimation", title=title, description=description)
        prompt += "\n\nReturn response as JSON with keys: needed (bool), difficulty, estimated_cost (float or null), notes."
        text = self.router.execute_task("repair_estimation", prompt)
        return self.parser.parse_as(text, RepairEstimateResponse)

    def analyze_risk(self, title: str, description: str, price: float) -> RiskAnalysisResponse:
        prompt = self.prompts.get_prompt(
            "risk_analysis", title=title, description=description, price=price
        )
        prompt += "\n\nReturn response as JSON with keys: risk_score (0-100), explanation, risk_factors (list of strings)."
        text = self.router.execute_task("risk_analysis", prompt)
        return self.parser.parse_as(text, RiskAnalysisResponse)

    def generate_recommendation(self, title: str, description: str, flipscore: float) -> str:
        prompt = self.prompts.get_prompt(
            "recommendation_generation", title=title, description=description, flipscore=flipscore
        )
        return self.router.execute_task("recommendation_generation", prompt).strip()

    def discover_opportunities(self, title: str, description: str) -> OpportunityAnalysisResponse:
        prompt = f"Analyze this marketplace listing for hidden opportunities:\nTitle: {title}\nDescription: {description}\n\n"
        prompt += "Identify factors like poor photos, generic titles, misspellings, wrong category, missing model numbers, or bundle listings.\n"
        prompt += "Return response as JSON with keys: has_misspellings (bool), is_wrong_category (bool), missing_model_number (bool), is_bundle (bool), poor_photos (bool), explanation (string), detected_factors (list of strings)."
        text = self.router.execute_task("opportunity_discovery", prompt)
        return self.parser.parse_as(text, OpportunityAnalysisResponse)
