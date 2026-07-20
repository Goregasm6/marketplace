from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from core.pipeline import BaseStage, PipelineContext, StageRegistry
from database.models import ListingStatus, QueueStatus, Opportunity
from database.schemas import ListingCreate, OpportunityCreate, QueueCreate

logger = logging.getLogger(__name__)


class ListingPipelineData(BaseModel):
    """Data object flowing through the listing pipeline."""

    listing: Optional[ListingCreate] = None
    raw_data: dict[str, Any] = Field(default_factory=dict)
    enriched_data: dict[str, Any] = Field(default_factory=dict)
    validation_errors: list[str] = Field(default_factory=list)
    scoring_results: dict[str, Any] = Field(default_factory=dict)
    opportunity_results: dict[str, Any] = Field(default_factory=dict)
    listing_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None


@StageRegistry.register("normalize")
class NormalizeStage(BaseStage[ListingPipelineData]):
    """Stage to normalize raw data into a ListingCreate object."""

    async def process(
        self, context: PipelineContext[ListingPipelineData]
    ) -> PipelineContext[ListingPipelineData]:
        raw = context.data.raw_data
        
        # Simple normalization logic - can be expanded
        title = raw.get("title", "").strip()
        price_str = str(raw.get("price", "0")).replace("$", "").replace(",", "").strip()
        try:
            price = float(price_str) if price_str else 0.0
        except ValueError:
            price = 0.0
            
        source = raw.get("source", "unknown")
        url = raw.get("url", "")
        external_id = raw.get("external_id") or url # Fallback to URL as external ID
        
        context.data.listing = ListingCreate(
            title=title,
            price=price,
            source=source,
            url=url,
            external_id=external_id,
            description=raw.get("description"),
        )
        return context


@StageRegistry.register("validate")
class ValidateStage(BaseStage[ListingPipelineData]):
    """Stage to validate the normalized listing."""

    async def process(
        self, context: PipelineContext[ListingPipelineData]
    ) -> PipelineContext[ListingPipelineData]:
        listing = context.data.listing
        if not listing:
            context.terminate("No listing data to validate")
            return context

        if not listing.title:
            context.data.validation_errors.append("Title is missing")
        if listing.price <= 0:
            # We allow 0 if it's truly free, but usually it's a mistake or "contact for price"
            context.data.validation_errors.append("Price must be greater than zero")
            
        if context.data.validation_errors:
            context.terminate(f"Validation failed: {context.data.validation_errors}")
            
        return context


@StageRegistry.register("persist")
class PersistStage(BaseStage[ListingPipelineData]):
    """Stage to persist the listing to the database."""

    def __init__(self, name: str | None = None, repository: Any = None) -> None:
        super().__init__(name)
        self.repository = repository

    async def process(
        self, context: PipelineContext[ListingPipelineData]
    ) -> PipelineContext[ListingPipelineData]:
        if not context.data.listing:
            context.terminate("No listing to persist")
            return context

        if not self.repository:
             from database.repositories import ListingRepository
             self.repository = ListingRepository()

        try:
            existing = self.repository.get_by_external_id(context.data.listing.external_id)
            if existing:
                context.data.listing_id = existing.id
                logger.info(f"Listing {existing.external_id} already exists, skipping persistence")
            else:
                db_listing = self.repository.create(context.data.listing)
                context.data.listing_id = db_listing.id
                logger.info(f"Persisted listing: {db_listing.id}")
        except Exception as e:
            logger.error(f"Failed to persist listing: {e}")
            context.terminate(f"Persistence error: {e}")

        return context


@StageRegistry.register("valuate")
class ValuateStage(BaseStage[ListingPipelineData]):
    """Stage to perform market valuation."""

    async def process(
        self, context: PipelineContext[ListingPipelineData]
    ) -> PipelineContext[ListingPipelineData]:
        from analysis.valuation.estimator import estimate_value
        
        if not context.data.listing:
            return context
            
        listing_dict = context.data.listing.model_dump()
        valuation = estimate_value(listing_dict)
        context.data.enriched_data["market_value"] = valuation.get("estimated_value")
        context.data.enriched_data["valuation_confidence"] = valuation.get("confidence")
        
        return context


@StageRegistry.register("score")
class ScoreStage(BaseStage[ListingPipelineData]):
    """Stage to calculate FlipScore."""

    async def process(
        self, context: PipelineContext[ListingPipelineData]
    ) -> PipelineContext[ListingPipelineData]:
        from analysis.flipscore import evaluate_listing
        
        if not context.data.listing:
            return context
            
        listing_dict = context.data.listing.model_dump()
        listing_dict.update(context.data.enriched_data)
        
        scoring = evaluate_listing(listing_dict)
        context.data.scoring_results = scoring
        
        return context


@StageRegistry.register("opportunity")
class OpportunityDetectionStage(BaseStage[ListingPipelineData]):
    """Stage to detect hidden opportunities."""

    async def process(
        self, context: PipelineContext[ListingPipelineData]
    ) -> PipelineContext[ListingPipelineData]:
        from analysis.opportunity import analyze_opportunity
        
        if not context.data.listing:
            return context
            
        listing_dict = context.data.listing.model_dump()
        listing_dict.update(context.data.enriched_data)
        listing_dict.update(context.data.scoring_results)
        
        opp_results = analyze_opportunity(listing_dict)
        context.data.opportunity_results = {
            "score": opp_results.opportunity_score,
            "explanation": opp_results.explanation,
        }
        
        return context


@StageRegistry.register("queue")
class QueueStage(BaseStage[ListingPipelineData]):
    """Stage to queue promising opportunities for review."""

    def __init__(self, name: str | None = None, opp_threshold: float = 70.0, score_threshold: float = 60.0) -> None:
        super().__init__(name)
        self.opp_threshold = opp_threshold
        self.score_threshold = score_threshold

    async def process(
        self, context: PipelineContext[ListingPipelineData]
    ) -> PipelineContext[ListingPipelineData]:
        if not context.data.listing_id:
            return context
            
        opp_score = context.data.opportunity_results.get("score", 0)
        flip_score = context.data.scoring_results.get("score", 0)
        
        if opp_score >= self.opp_threshold or flip_score >= self.score_threshold:
            from database.repositories import OpportunityRepository
            from database.models import Opportunity
            
            opp_repo = OpportunityRepository()
            
            # Use raw model for creation as the repo expects the model instance or we can wrap it
            opp_model = Opportunity(
                listing_id=context.data.listing_id,
                potential_profit=context.data.enriched_data.get("market_value", 0) - (context.data.listing.price if context.data.listing else 0),
                confidence_score=context.data.scoring_results.get("confidence", 0.5),
                notes=context.data.opportunity_results.get("explanation")
            )
            
            db_opp = opp_repo.create(opp_model)
            context.data.opportunity_id = db_opp.id
            logger.info(f"Queued opportunity: {db_opp.id}")
            
        return context


@StageRegistry.register("notify")
class NotifyStage(BaseStage[ListingPipelineData]):
    """Stage to notify about new opportunities."""

    async def process(
        self, context: PipelineContext[ListingPipelineData]
    ) -> PipelineContext[ListingPipelineData]:
        if not context.data.opportunity_id:
            return context
            
        logger.info(f"Notification triggered for opportunity {context.data.opportunity_id}")
        # Integration with existing notification plugins would happen here
        
        return context
