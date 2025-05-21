"""CLI commands for managing and checking API costs."""
import click
from rich import box
from rich.console import Console
from rich.table import Table

from ..cli import cli as main_cli
from ..core.cost_tracker import cost_tracker, get_usage_summary

console = Console()


@click.group()
def costs():
    """Manage and check API costs."""
    pass


@costs.command()
def show():
    """Show current month's API usage and costs."""
    summary = get_usage_summary()

    table = Table(title=f"API Usage for {summary['month']}", box=box.ROUNDED)

    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green", justify="right")

    table.add_row("Total Searches", str(summary["total_searches"]))
    table.add_row("Total Cost", f"${summary['total_cost']:.2f}")

    if summary["total_searches"] > 0:
        table.add_row("Avg. Cost/Search", f"${summary['average_cost_per_search']:.4f}")

    console.print(table)


@costs.command()
@click.option("--all", "-a", is_flag=True, help="Show all historical data")
def history(all: bool):
    """Show historical API usage and costs."""
    if all:
        historical_data = cost_tracker.get_historical_usage()
        table = Table(title="Historical API Usage", box=box.ROUNDED)

        table.add_column("Month", style="cyan")
        table.add_column("Searches", style="green", justify="right")
        table.add_column("Total Cost", style="green", justify="right")

        for month_data in historical_data:
            table.add_row(
                month_data["month"],
                str(month_data["total_searches"]),
                f"${month_data['total_cost']:.2f}",
            )

        console.print(table)
    else:
        show()


# Add the costs command group to the main CLI

main_cli.add_command(costs, name="costs")
