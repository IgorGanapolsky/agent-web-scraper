"""
Modern CLI interface for Agent Web Scraper using Typer.
"""

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from app.config.safe_logger import get_structured_logger
from app.observability import health_check

app = typer.Typer(
    name="agent-scraper",
    help="AI-powered market research agent for automated web scraping and analysis",
    rich_markup_mode="rich",
)

console = Console()
logger = get_structured_logger(__name__)


@app.command()
def health() -> None:
    """Check application health status."""
    console.print("[bold blue]🏥 Agent Web Scraper Health Check[/bold blue]")

    health_data = health_check()

    # Create a table for health status
    table = Table(title="Health Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")

    # Overall status
    status_color = (
        "green"
        if health_data["status"] == "healthy"
        else "yellow" if health_data["status"] == "degraded" else "red"
    )
    table.add_row(
        "Overall", f"[{status_color}]{health_data['status'].upper()}[/{status_color}]"
    )

    # Individual checks
    for check_name, check_status in health_data["checks"].items():
        status_color = (
            "green"
            if check_status == "ok"
            else "yellow" if "not_" in check_status else "red"
        )
        table.add_row(
            check_name.title(), f"[{status_color}]{check_status}[/{status_color}]"
        )

    console.print(table)

    # Additional info
    console.print(f"\n[dim]Version: {health_data['version']}[/dim]")
    console.print(f"[dim]Environment: {health_data['environment']}[/dim]")


@app.command()
def setup(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force setup even if already configured"
    ),
) -> None:
    """Set up the development environment."""
    console.print("[bold blue]🚀 Setting up Agent Web Scraper...[/bold blue]")

    # Check if already set up
    if Path("pyproject.toml").exists() and not force:
        console.print(
            "[yellow]⚠️  Project appears to be already set up. Use --force to override.[/yellow]"
        )
        raise typer.Exit(1)

    # Run the setup script
    setup_script = Path(__file__).parent.parent.parent / "setup_dev.py"
    if setup_script.exists():
        import subprocess

        result = subprocess.run([f"{setup_script}"], shell=True)
        if result.returncode == 0:
            console.print("[green]✅ Setup completed successfully![/green]")
        else:
            console.print("[red]❌ Setup failed![/red]")
            raise typer.Exit(1)
    else:
        console.print("[red]❌ Setup script not found![/red]")
        raise typer.Exit(1)


@app.command()
def info() -> None:
    """Display project information."""
    from app import __author__, __version__

    console.print(f"[bold blue]Agent Web Scraper v{__version__}[/bold blue]")
    console.print(f"Author: {__author__}")
    console.print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")

    # Show configuration
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    config_items = [
        ("Log Level", os.getenv("LOG_LEVEL", "INFO")),
        ("Log Format", os.getenv("LOG_FORMAT", "json")),
        ("Sentry Enabled", "Yes" if os.getenv("SENTRY_DSN") else "No"),
        ("Environment", os.getenv("ENVIRONMENT", "development")),
        ("Debug Mode", os.getenv("DEBUG", "false")),
    ]

    for setting, value in config_items:
        table.add_row(setting, str(value))

    console.print(table)


if __name__ == "__main__":
    app()
