from __future__ import annotations

from analysis.ai_interfaces import AIPlugin, AnalysisArtifacts, ListingContext
from config.settings import settings
from core.ai.tasks import AIService


class LLMAnalysisPlugin(AIPlugin):
    """Plugin that uses LLM to enrich listing data."""

    name: str = "llm_analysis"

    def __init__(self, service: AIService | None = None):
        self.service = service or AIService()

    def run(
        self, context: ListingContext, artifacts: AnalysisArtifacts
    ) -> AnalysisArtifacts:
        if not settings.ai_enabled:
            return artifacts

        # Perform high-level summary if not already present
        if not artifacts.llm_summary and context.description:
            artifacts.llm_summary = self.service.cleanup_description(
                context.description
            )

        # Generate recommendation if not present
        if not artifacts.recommendation and context.title:
            # We might need a flipscore here, but let's assume it's calculated elsewhere or passed in context raw_data
            flipscore = context.raw_data.get("flipscore", 0.0)
            artifacts.recommendation = self.service.generate_recommendation(
                context.title or "", context.description or "", flipscore
            )

        # Add more logic as needed for other tasks
        # For example, repair estimation
        if context.title and context.description:
            repair_est = self.service.estimate_repair(
                context.title, context.description
            )
            if repair_est.needed:
                artifacts.raw_data["repair_estimate"] = repair_est.model_dump()

        return artifacts
