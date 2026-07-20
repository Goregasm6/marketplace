from __future__ import annotations

from typing import Any, Callable, Protocol, runtime_checkable


@runtime_checkable
class BaseScheduler(Protocol):
    """Protocol defining the interface for all scheduler backends."""

    def start(self) -> None:
        """Start the scheduler."""
        ...

    def stop(self, wait: bool = True) -> None:
        """Stop the scheduler."""
        ...

    def pause(self) -> None:
        """Pause the scheduler."""
        ...

    def resume(self) -> None:
        """Resume the scheduler."""
        ...

    def status(self) -> dict[str, Any]:
        """Get the current status of the scheduler."""
        ...

    def schedule(
        self,
        func: Callable[..., Any],
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
        *,
        job_id: str | None = None,
        name: str | None = None,
        trigger: str = "interval",
        **trigger_kwargs: Any,
    ) -> str:
        """
        Schedule a task.

        Args:
            func: The function to execute.
            args: Positional arguments for the function.
            kwargs: Keyword arguments for the function.
            job_id: Unique identifier for the job.
            name: Human-readable name for the job.
            trigger: Type of trigger (e.g., "interval", "cron").
            **trigger_kwargs: Arguments for the trigger.

        Returns:
            The job ID.
        """
        ...

    def cancel(self, job_id: str) -> bool:
        """
        Cancel a scheduled task.

        Args:
            job_id: The ID of the job to cancel.

        Returns:
            True if the job was cancelled, False otherwise.
        """
        ...
