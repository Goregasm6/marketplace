"""Core domain abstractions for MAIE."""

from __future__ import annotations

__all__ = ["SchedulerService"]


def __getattr__(name: str):
    if name == "SchedulerService":
        from core.scheduler import SchedulerService

        return SchedulerService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
