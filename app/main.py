import typer
from loguru import logger

from app.config import LOGGING_LEVEL
from config.settings import settings
from core.scheduler import SchedulerService
from database.database import initialize_database

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.callback()
def main() -> None:
    """Initialize the local database before running commands."""
    initialize_database()


@app.command()
def hello() -> None:
    """Simple placeholder command for scaffold validation."""
    logger.info("MAIE scaffold is ready")
    typer.echo(f"Hello from {settings.app_name}!")


scheduler_app = typer.Typer(help="Manage the runtime scheduler")
app.add_typer(scheduler_app, name="scheduler")


@scheduler_app.command("status")
def scheduler_status() -> None:
    """Show scheduler configuration and recent execution metrics."""
    service = SchedulerService(settings=settings)
    payload = service.status()
    typer.echo(f"Scheduler running: {payload['running']}")
    typer.echo(f"Enabled collectors: {', '.join(payload['enabled_collectors']) or 'none'}")
    typer.echo(f"Interval (minutes): {payload['interval_minutes']}")
    typer.echo(f"Metrics recorded: {payload['metrics_count']}")
    if payload["latest_metrics"]:
        for metric in payload["latest_metrics"]:
            typer.echo(f"- {metric['collector']}: {metric['status']} ({metric['attempts']} attempts)")


@scheduler_app.command("run")
def scheduler_run(collector_name: str = typer.Argument(..., help="Collector name to execute once")) -> None:
    """Run a collector job immediately."""
    service = SchedulerService(settings=settings)
    result = service.run_job(collector_name)
    typer.echo(f"{result['collector']}: {result['status']}")


@scheduler_app.command("start")
def scheduler_start() -> None:
    """Start the background scheduler for all enabled collectors."""
    service = SchedulerService(settings=settings)
    service.start()
    typer.echo("Scheduler started")


@scheduler_app.command("stop")
def scheduler_stop() -> None:
    """Stop the background scheduler."""
    service = SchedulerService(settings=settings)
    service.shutdown()
    typer.echo("Scheduler stopped")


logger.remove()
logger.add("logs/maie.log", rotation="1 day", level=LOGGING_LEVEL, serialize=True)


if __name__ == "__main__":
    app()
