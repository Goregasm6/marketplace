from __future__ import annotations

from typing import Any, Callable

from core.scheduler_base import BaseScheduler


class FutureCeleryBackend(BaseScheduler):
    """Placeholder for future Celery implementation."""

    def start(self) -> None:
        raise NotImplementedError("Celery backend is not yet implemented.")

    def stop(self, wait: bool = True) -> None:
        pass

    def pause(self) -> None:
        pass

    def resume(self) -> None:
        pass

    def status(self) -> dict[str, Any]:
        return {"type": "celery", "running": False, "status": "not_implemented"}

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
        raise NotImplementedError("Celery backend is not yet implemented.")

    def cancel(self, job_id: str) -> bool:
        return False


class FutureRQBackend(BaseScheduler):
    """Placeholder for future RQ implementation."""

    def start(self) -> None:
        raise NotImplementedError("RQ backend is not yet implemented.")

    def stop(self, wait: bool = True) -> None:
        pass

    def pause(self) -> None:
        pass

    def resume(self) -> None:
        pass

    def status(self) -> dict[str, Any]:
        return {"type": "rq", "running": False, "status": "not_implemented"}

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
        raise NotImplementedError("RQ backend is not yet implemented.")

    def cancel(self, job_id: str) -> bool:
        return False
