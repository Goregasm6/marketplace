"""Pipeline Engine for MAIE listing lifecycle.

The Pipeline Engine orchestrates the execution of modular stages that process
marketplace listings from raw discovery to notification.

Execution Flow:
1. Initialize PipelineContext with the input data (T).
2. For each stage in the pipeline:
   a. Check if the context is terminated. If so, stop.
   b. Record start time for metrics.
   c. Execute stage.process(context).
   d. A stage may enrich the data, terminate processing, or raise an exception.
   e. Capture metrics (success, execution time, errors).
3. Return the final PipelineContext.

Stages are pluggable and can be registered using the @StageRegistry.register decorator.
Pipelines can be constructed manually or from a configuration list.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


@dataclass
class PipelineMetrics:
    """Execution metrics for a pipeline stage."""

    stage_name: str
    execution_time_ms: float = 0.0
    success: bool = True
    error: str | None = None
    retries: int = 0


@dataclass
class PipelineContext(Generic[T]):
    """Context passed through the pipeline stages."""

    data: T
    metadata: dict[str, Any] = field(default_factory=dict)
    metrics: list[PipelineMetrics] = field(default_factory=list)
    terminated: bool = False
    termination_reason: str | None = None

    def terminate(self, reason: str) -> None:
        """Stop further pipeline execution."""
        self.terminated = True
        self.termination_reason = reason


class BaseStage(ABC, Generic[T]):
    """Base class for all pipeline stages."""

    name: str = ""

    def __init__(self, name: str | None = None) -> None:
        self.name = name or self.name or self.__class__.__name__

    @abstractmethod
    async def process(self, context: PipelineContext[T]) -> PipelineContext[T]:
        """Process the data in the context."""
        pass


class StageRegistry:
    """Registry for pipeline stages."""

    _stages: dict[str, type[BaseStage[Any]]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type[BaseStage[Any]]], type[BaseStage[Any]]]:
        def wrapper(stage_cls: type[BaseStage[Any]]) -> type[BaseStage[Any]]:
            cls._stages[name.lower()] = stage_cls
            return stage_cls

        return wrapper

    @classmethod
    def get(cls, name: str) -> type[BaseStage[Any]] | None:
        return cls._stages.get(name.lower())


class PipelineEngine(Generic[T]):
    """Orchestrates the execution of a series of pipeline stages."""

    def __init__(self, stages: list[BaseStage[T]] | None = None) -> None:
        self.stages = stages or []

    @classmethod
    def from_config(cls, stage_names: list[str | dict[str, Any]]) -> PipelineEngine[T]:
        """Create a pipeline engine from a list of stage names and optional configs."""
        stages = []
        for item in stage_names:
            if isinstance(item, str):
                name = item
                config = {}
            else:
                name = list(item.keys())[0]
                config = item[name]

            stage_cls = StageRegistry.get(name)
            if stage_cls:
                stages.append(stage_cls(**config))
            else:
                logger.warning(f"Stage '{name}' not found in registry")

        return cls(stages)

    def add_stage(self, stage: BaseStage[T]) -> None:
        """Add a stage to the pipeline."""
        self.stages.append(stage)

    async def execute(self, initial_data: T) -> PipelineContext[T]:
        """Execute all stages in order."""
        context = PipelineContext(data=initial_data)

        for stage in self.stages:
            if context.terminated:
                logger.info(
                    f"Pipeline terminated before stage {stage.name}: {context.termination_reason}"
                )
                break

            start_time = time.perf_counter()
            metrics = PipelineMetrics(stage_name=stage.name)

            try:
                logger.debug(f"Executing pipeline stage: {stage.name}")
                context = await stage.process(context)
                metrics.success = True
            except Exception as e:
                logger.exception(f"Error in pipeline stage {stage.name}: {e}")
                metrics.success = False
                metrics.error = str(e)
                # By default, we might want to terminate on unhandled exceptions
                context.terminate(f"Error in {stage.name}: {e}")
            finally:
                metrics.execution_time_ms = (time.perf_counter() - start_time) * 1000
                context.metrics.append(metrics)

        return context
