from datetime import date

import typer

from src.db import get_session_factory
from src.ingestion.client import UFCStatsClient
from src.ingestion.config import DEFAULT_DELAY
from src.ingestion.orchestrator import run_ingestion
from src.logging_config import setup_logging

app = typer.Typer(help="UFC Data Analytics CLI")


@app.callback()
def main() -> None:
    pass


@app.command("ingest")
def ingest(
    date_from: str = typer.Option(None, help="Start date (YYYY-MM-DD)"),
    date_to: str = typer.Option(None, help="End date (YYYY-MM-DD)"),
    delay: float = typer.Option(DEFAULT_DELAY, help="Seconds between HTTP requests"),
) -> None:
    setup_logging()

    parsed_from = date.fromisoformat(date_from) if date_from else None
    parsed_to = date.fromisoformat(date_to) if date_to else None

    session_factory = get_session_factory()
    client = UFCStatsClient(delay=delay)

    try:
        state = run_ingestion(session_factory, client, parsed_from, parsed_to)
    finally:
        client.close()

    typer.echo(f"\nIngestion {state.status}")
    typer.echo(f"  Events:      {state.events_inserted} inserted, {state.events_updated} updated")
    typer.echo(f"  Fighters:    {state.fighters_inserted} inserted, {state.fighters_updated} updated")
    typer.echo(f"  Fights:      {state.fights_inserted} inserted, {state.fights_updated} updated")
    typer.echo(f"  Fight stats: {state.fight_stats_inserted} inserted, {state.fight_stats_updated} updated")

    if state.error_message:
        typer.echo(f"  Error: {state.error_message}")


@app.command("check-quality")
def check_quality() -> None:
    setup_logging()

    from src.ingestion.quality import run_all_checks

    session = get_session_factory()()
    try:
        results = run_all_checks(session)
    finally:
        session.close()

    total_issues = sum(len(v) for v in results.values())
    for name, issues in results.items():
        status = "PASS" if not issues else "FAIL"
        typer.echo(f"  [{status}] {name}: {len(issues)} issues")
        for issue in issues[:5]:
            typer.echo(f"         {issue}")

    typer.echo(f"\nTotal: {total_issues} issues")


if __name__ == "__main__":
    app()
