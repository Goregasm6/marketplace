from __future__ import annotations

from typing import Any

from typer.testing import CliRunner

from app.main import app
from collectors.base import BaseCollector
from config.settings import Settings
from core.scheduler import SchedulerService


class RecordingCollector(BaseCollector):
    name = "recording"

    def __init__(self, *, fail_once: bool = False) -> None:
        self.calls = 0
        self.fail_once = fail_once

    def search(self, query: str, **kwargs: Any) -> Any:
        return []

    def fetch(self, search_results: Any, **kwargs: Any) -> Any:
        return []

    def normalize(self, item: Any, **kwargs: Any) -> Any:
        return item

    def validate(self, item: Any, **kwargs: Any) -> bool:
        return True

    def save(self, items: Any, **kwargs: Any) -> Any:
        self.calls += 1
        return list(items)

    def run(self, query: str, **kwargs: Any) -> Any:
        if self.fail_once and self.calls == 0:
            self.calls += 1
            raise RuntimeError("boom")
        self.calls += 1
        return self.calls


class FakeScheduler:
    def __init__(self) -> None:
        self.jobs: list[dict[str, Any]] = []
        self.started = False

    def add_job(self, func, **kwargs: Any) -> None:
        self.jobs.append({"func": func, **kwargs})

    def remove_job(self, job_id: str) -> None:
        self.jobs = [job for job in self.jobs if job.get("id") != job_id]

    def start(self) -> None:
        self.started = True

    def shutdown(self, wait: bool = True) -> None:
        self.started = False

    def get_jobs(self) -> list[dict[str, Any]]:
        return list(self.jobs)


def test_scheduler_executes_enabled_collectors_and_records_metrics() -> None:
    collector = RecordingCollector()
    settings = Settings(enabled_collectors=["recording"], search_interval=2)
    service = SchedulerService(
        settings=settings,
        collectors={"recording": collector},
        scheduler_factory=lambda: FakeScheduler(),
    )

    service.start()
    result = service.run_job("recording")

    assert collector.calls == 1
    assert result["status"] == "success"
    assert result["collector"] == "recording"
    assert service.metrics[-1]["status"] == "success"


def test_scheduler_skips_overlapping_jobs() -> None:
    collector = RecordingCollector()
    settings = Settings(enabled_collectors=["recording"], search_interval=2)
    service = SchedulerService(
        settings=settings,
        collectors={"recording": collector},
        scheduler_factory=lambda: FakeScheduler(),
    )

    service._job_locks["recording"].acquire()
    result = service._run_job_safe("recording")

    assert result["status"] == "skipped"
    assert collector.calls == 0


def test_scheduler_retries_failed_jobs_with_backoff(monkeypatch: Any) -> None:
    collector = RecordingCollector(fail_once=True)
    settings = Settings(enabled_collectors=["recording"], search_interval=2)
    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr("core.scheduler.time.sleep", fake_sleep)

    service = SchedulerService(
        settings=settings,
        collectors={"recording": collector},
        scheduler_factory=lambda: FakeScheduler(),
        retry_attempts=2,
        retry_backoff_base_seconds=1.0,
    )

    result = service._execute_collector("recording")

    assert collector.calls == 2
    assert result["status"] == "success"
    assert sleeps == [1.0]


def test_scheduler_cli_exposes_status_command() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["scheduler", "status"])

    assert result.exit_code == 0
    assert "Scheduler" in result.output
