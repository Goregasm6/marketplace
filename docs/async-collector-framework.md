# Asynchronous Collector Framework

This document describes the design and behavior of the asynchronous collector framework in MAIE.

## Lifecycle

Each collector follows a structured lifecycle executed by the `SchedulerService`:

1.  **Registration**: Collectors are automatically registered via `__init_subclass__` and discovered by the registry.
2.  **Scheduling**: The `SchedulerService` adds jobs to the `AsyncIOScheduler` based on the configured `search_interval`.
3.  **Triggering**: When a job is triggered:
    -   The `SchedulerService` attempts to acquire a per-collector `asyncio.Lock` to prevent overlapping executions of the same collector.
    -   It then acquires a global `asyncio.Semaphore` to limit the total number of collectors running concurrently.
4.  **Execution**: The `BaseCollector.run()` method orchestrates the pipeline:
    -   `search()`: Fetches raw data (Async).
    -   `fetch()`: Extracts item payloads (Async).
    -   `normalize()`: Converts payloads to `Listing` models (Async).
    -   `validate()`: Filters out invalid listings (Async).
    -   `save()`: Persists the results (Async).
5.  **Completion**: Locks and semaphore slots are released, and metrics are recorded.

## Concurrency Model

-   **Overlapping Protection**: Each collector has a dedicated `asyncio.Lock`. If a collector is still running when its next interval triggers, the new execution is skipped.
-   **Resource Limiting**: A global `asyncio.Semaphore` (configured via `max_concurrent_collectors`) limits how many collectors can execute their `_execute_collector` logic simultaneously.
-   **Non-blocking IO**: All network operations must use `asyncio` and the shared `NetworkClient` to avoid blocking the event loop.

## Error Handling

-   **Retries**: The `SchedulerService` implements exponential backoff retries for collector execution.
-   **Isolation**: Failures in one collector do not affect others.
-   **Metrics**: Successes, failures, skips, and durations are recorded in the `SchedulerService.metrics`.

## Cancellation

-   Collectors should respect `asyncio` cancellation. Long-running loops should occasionally yield control or check for cancellation if necessary.
-   The `SchedulerService.shutdown()` method stops the scheduler and waits for active jobs if requested.

## Retry Behavior

-   **Backoff**: Uses exponential backoff: `retry_backoff_base_seconds * (2 ** (attempt - 1))`.
-   **Max Attempts**: Configurable via `retry_attempts` in `SchedulerService`.
-   **Network Retries**: The `NetworkClient` also implements its own retry logic for transient HTTP failures.
