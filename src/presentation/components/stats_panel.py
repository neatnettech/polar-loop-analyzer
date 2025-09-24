from textual.widget import Widget
from textual.reactive import reactive
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.console import Console, ConsoleOptions, RenderResult
from typing import Dict, Any, Optional


class StatsPanel(Widget):
    """Statistics panel component."""

    stats = reactive({}, layout=True)
    title = reactive("Statistics", layout=False)

    def __init__(self, stats: Dict[str, Any] = None, title: str = "Statistics", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        if stats:
            self.stats = stats

    def render(self) -> Panel:
        if not self.stats:
            return Panel(
                Text("No statistics available", justify="center"),
                title=self.title,
                border_style="yellow"
            )

        table = Table(show_header=False, show_edge=False, expand=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="white")

        # Format stats for display
        for key, value in self.stats.items():
            display_key = key.replace("_", " ").title()

            if value is None:
                display_value = "N/A"
            elif isinstance(value, float):
                display_value = f"{value:.1f}"
            elif isinstance(value, str):
                display_value = value
            else:
                display_value = str(value)

            # Add color coding for certain metrics
            if "zone" in key.lower() and value:
                if value == "Maximum":
                    display_value = f"[red]{display_value}[/red]"
                elif value == "Hard":
                    display_value = f"[orange1]{display_value}[/orange1]"
                elif value == "Moderate":
                    display_value = f"[yellow]{display_value}[/yellow]"
                elif value == "Light":
                    display_value = f"[green]{display_value}[/green]"
                elif value == "Rest":
                    display_value = f"[blue]{display_value}[/blue]"

            if "trend" in key.lower() and value:
                if value == "increasing":
                    display_value = f"[red]↑ {display_value}[/red]"
                elif value == "decreasing":
                    display_value = f"[blue]↓ {display_value}[/blue]"
                else:
                    display_value = f"[green]→ {display_value}[/green]"

            table.add_row(display_key, display_value)

        return Panel(
            table,
            title=self.title,
            border_style="yellow"
        )

    def update_stats(self, new_stats: Dict[str, Any]):
        """Update statistics."""
        self.stats = new_stats