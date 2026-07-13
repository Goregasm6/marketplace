from __future__ import annotations

import time
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable

from loguru import logger

from collectors.base import BaseCollector, CollectorRegistry, discover_collectors
from config.settings import Settings, settings as default_settings


class SchedulerService:
    """Coordinate collector execution with retries, overlap protection, and metrics."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        collectors: dict[str, BaseCollector] | None = None,
        scheduler_factory: Callable[[], Any] | None = None,
        retry_attempts: int = 3,
        retry_backoff_base_seconds: float = 1.0,
    ) -> None:
        self.settings = settings or default_settings
        self.collectors = collectors or {}
        self.scheduler_factory = scheduler_factory or self._create_scheduler
        self.retry_attempts = retry_attempts
        self.retry_backoff_base_seconds = retry_backoff_base_seconds
        self.scheduler: Any | None = None
        self._job_locks: dict[str, Lock] = {}
        self.metrics: list[dict[str, Any]] = []
        self._logger = logger.bind(component="scheduler_service")

        self._initialize_job_locks()

    def _initialize_job_locks(self) -> None:
        enabled_collectors = [name for name in self.settings.enabled_collectors if str(name).strip()]
        for name in enabled_collectors:
            self._job_locks.setdefault(name.lower(), Lock())

    def _create_scheduler(self) -> Any:
        from apscheduler.schedulers.background import BackgroundScheduler

        return BackgroundScheduler(timezone=timezone.utc, job_defaults={"coalesce": True, "max_instances": 1})

    def _resolve_collectors(self) -> dict[str, BaseCollector]:
        resolved: dict[str, BaseCollector] = dict(self.collectors)
        if resolved:
            return resolved

        for collector_cls in discover_collectors():
            collector_name = getattr(collector_cls, "name", None) or collector_cls.__name__
            resolved[collector_name.lower()] = collector_cls()
        return resolved

    def _get_collector(self, collector_name: str) -> BaseCollector | None:
        normalized_name = collector_name.lower()
        resolved = self._resolve_collectors()
        collector = resolved.get(normalized_name)
        if collector is None:
            registry_cls = CollectorRegistry.get(normalized_name)
            if registry_cls is None:
                return None
            collector = registry_cls()
        return collector

    def start(self) -> Any:
        if self.scheduler is not None:
            return self.scheduler

        self.scheduler = self.scheduler_factory()
        self._logger.info(
            "scheduler.started",
            enabled_collectors=list(self.settings.enabled_collectors),
            interval_minutes=self.settings.search_interval,
        )

        for collector_name in self.settings.enabled_collectors:
            normalized_name = str(collector_name).strip().lower()
            if not normalized_name:
                continue
            self._job_locks.setdefault(normalized_name, Lock())
            self.scheduler.add_job(
                self._run_job_safe,
                args=[normalized_name],
                id=f"collector:{normalized_name}",
                name=normalized_name,
                trigger="interval",
                minutes=self.settings.search_interval,
                replace_existing=True,
                coalesce=True,
                max_instances=1,
            )

        self.scheduler.start()
        return self.scheduler

    def shutdown(self, wait: bool = True) -> None:
        if self.scheduler is None:
            return
        self.scheduler.shutdown(wait=wait)
        self.scheduler = None
        self._logger.info("scheduler.stopped")

    def status(self) -> dict[str, Any]:
        scheduler_running = self.scheduler is not None and getattr(self.scheduler, "running", False)
        return {
            "running": scheduler_running,
            "enabled_collectors": list(self.settings.enabled_collectors),
            "interval_minutes": self.settings.search_interval,
            "metrics_count": len(self.metrics),
            "latest_metrics": list(self.metrics[-3:]),
        }

    def _run_job_safe(self, collector_name: str) -> dict[str, Any]:
        normalized_name = collector_name.lower()
        lock = self._job_locks.setdefault(normalized_name, Lock())
        if not lock.acquire(blocking=False):
            self._logger.info("scheduler.job_skipped", collector=normalized_name, reason="already_running")
            self._record_metric(normalized_name, "skipped", attempts=0, duration_seconds=0.0)
            return {"collector": normalized_name, "status": "skipped", "attempts": 0}

        try:
            return self._execute_collector(normalized_name)
        finally:
            lock.release()

    def run_job(self, collector_name: str) -> dict[str, Any]:
        return self._run_job_safe(collector_name)

    def _execute_collector(self, collector_name: str) -> dict[str, Any]:
        collector = self._get_collector(collector_name)
        if collector is None:
            error = f"Collector {collector_name} is not available"
            self._logger.error("scheduler.job_failed", collector=collector_name, error=error)
            self._record_metric(collector_name, "failed", attempts=1, duration_seconds=0.0, error=error)
            return {"collector": collector_name, "status": "failed", "attempts": 1, "error": error}

        started_at = time.perf_counter()
        last_error: Exception | None = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                self._logger.info("scheduler.job_started", collector=collector_name, attempt=attempt)
                collector.run(query="")
                duration_seconds = round(time.perf_counter() - started_at, 6)
                self._logger.info(
                    "scheduler.job_succeeded",
                    collector=collector_name,
                    attempt=attempt,
                    duration_seconds=duration_seconds,
                )
                self._record_metric(collector_name, "success", attempts=attempt, duration_seconds=duration_seconds)
                return {"collector": collector_name, "status": "success", "attempts": attempt, "duration_seconds": duration_seconds}
            except Exception as exc:  # pragma: no cover - exercised through retry loop
                last_error = exc
                if attempt >= self.retry_attempts:
                    break
                delay_seconds = self.retry_backoff_base_seconds * (2 ** (attempt - 1))
                self._logger.warning(
                    "scheduler.job_retry",
                    collector=collector_name,
                    attempt=attempt,
                    delay_seconds=delay_seconds,
                    error=str(exc),
                )
                time.sleep(delay_seconds)

        duration_seconds = round(time.perf_counter() - started_at, 6)
        error = str(last_error) if last_error is not None else "Unknown collector failure"
        self._logger.error("scheduler.job_failed", collector=collector_name, attempts=self.retry_attempts, error=error)
        self._record_metric(collector_name, "failed", attempts=self.retry_attempts, duration_seconds=duration_seconds, error=error)
        return {"collector": collector_name, "status": "failed", "attempts": self.retry_attempts, "error": error}

    def _record_metric(
        self,
        collector_name: str,
        status: str,
        *,
        attempts: int,
        duration_seconds: float,
        error: str | None = None,
    ) -> None:
        self.metrics.append(
            {
                "collector": collector_name,
                "status": status,
                "attempts": attempts,
                "duration_seconds": duration_seconds,
                "error": error,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )


__all__ = ["SchedulerService"]
