from textual.widget import Widget
from textual.reactive import reactive
from rich.console import Console, ConsoleOptions, RenderResult
from rich.panel import Panel
from rich.text import Text
import plotext as plt
from typing import List, Tuple, Optional
from io import StringIO


class HeartRateGraph(Widget):
    """Heart rate graph component using plotext."""

    data = reactive([], layout=True)
    title = reactive("Heart Rate", layout=False)

    def __init__(self, data: List[Tuple[int, float]] = None, **kwargs):
        super().__init__(**kwargs)
        if data:
            self.data = data

    def render(self) -> Panel:
        if not self.data:
            return Panel(
                Text("No heart rate data available", justify="center"),
                title=self.title,
                border_style="blue"
            )

        # Create plot
        output = StringIO()
        plt.clf()
        plt.theme("dark")

        hours = [d[0] for d in self.data]
        rates = [d[1] for d in self.data]

        plt.plot(hours, rates, marker="braille", color="red")
        plt.title(self.title)
        plt.xlabel("Hour of Day")
        plt.ylabel("BPM")

        # Set size based on terminal
        plt.plotsize(60, 15)
        plt.grid(True, True)

        # Draw to string
        plt.build()
        plot_str = plt.build()

        return Panel(
            Text(plot_str),
            title=self.title,
            border_style="red"
        )

    def update_data(self, new_data: List[Tuple[int, float]]):
        """Update graph data."""
        self.data = new_data