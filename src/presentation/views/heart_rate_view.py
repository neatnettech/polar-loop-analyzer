from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Label
from textual.reactive import reactive
from textual.timer import Timer
from rich.panel import Panel
import plotext as plt
from typing import Optional
from datetime import datetime


class HeartRateView(Container):
    """Heart Rate detailed view with graphs."""

    def __init__(self, facade, **kwargs):
        super().__init__(**kwargs)
        self.facade = facade
        self.timer: Optional[Timer] = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the heart rate view."""
        yield Vertical(
            Label("❤️ Heart Rate Analysis", id="hr_title"),
            Static(id="hr_current_detailed"),
            Static(id="hr_trend_graph"),
            Static(id="hr_zones_graph"),
            Horizontal(
                Static(id="hr_hourly_stats"),
                Static(id="hr_variability"),
                classes="hr-stats-row"
            ),
            classes="heart-rate-view"
        )

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.update_heart_rate_view()
        # Update every 10 seconds for detailed view
        self.timer = self.set_interval(10, self.update_heart_rate_view)

    def update_heart_rate_view(self) -> None:
        """Update all heart rate components."""
        try:
            data = self.facade.get_dashboard_data()

            # Update detailed current HR
            hr_current_widget = self.query_one("#hr_current_detailed", Static)
            hr_current_widget.update(self.create_detailed_hr_panel(data["current_hr"]))

            # Update trend graph
            trend_widget = self.query_one("#hr_trend_graph", Static)
            trend_widget.update(self.create_hr_trend_graph(data["hourly_data"]))

            # Update zones graph
            zones_graph_widget = self.query_one("#hr_zones_graph", Static)
            zones_graph_widget.update(self.create_zones_graph(data["zone_distribution"]))

            # Update hourly stats
            hourly_widget = self.query_one("#hr_hourly_stats", Static)
            hourly_widget.update(self.create_hourly_stats(data["hourly_data"]))

            # Update HRV info
            hrv_widget = self.query_one("#hr_variability", Static)
            hrv_widget.update(self.create_hrv_panel(data["hrv"], data["trend"]))

        except Exception as e:
            self.query_one("#hr_trend_graph", Static).update(
                Panel(f"Error updating heart rate view: {str(e)}", title="Error", border_style="red")
            )

    def create_detailed_hr_panel(self, hr_data):
        """Create detailed heart rate panel."""
        from rich.table import Table

        table = Table(show_header=False, expand=True, box=None)
        table.add_column("Metric", style="cyan", width=15)
        table.add_column("Value", justify="center", style="bold red", width=15)
        table.add_column("Metric", style="cyan", width=15)
        table.add_column("Value", justify="center", style="yellow", width=15)

        if not hr_data or hr_data.get("current_hr") is None:
            return Panel("No heart rate data available", title="Current Heart Rate", border_style="red")

        zone = hr_data.get('zone', 'N/A')
        zone_color = hr_data.get('zone_color', 'white')

        table.add_row(
            "❤️ Current HR", f"{hr_data.get('current_hr', 'N/A')} BPM",
            "📊 Average", f"{hr_data.get('avg_hr', 'N/A')} BPM"
        )
        table.add_row(
            "📉 Minimum", f"{hr_data.get('min_hr', 'N/A')} BPM",
            "📈 Maximum", f"{hr_data.get('max_hr', 'N/A')} BPM"
        )
        table.add_row(
            "🎯 Zone", f"[{zone_color}]{zone}[/{zone_color}]",
            "📍 Trend", hr_data.get('trend', 'N/A').title()
        )

        return Panel(table, title="Current Heart Rate Status", border_style="red")

    def create_hr_trend_graph(self, hourly_data):
        """Create heart rate trend graph."""
        if not hourly_data:
            return Panel("No heart rate data available", title="24-Hour Trend", border_style="blue")

        plt.clf()
        plt.theme("dark")

        hours = [d[0] for d in hourly_data]
        rates = [d[1] for d in hourly_data]

        plt.plot(hours, rates, marker="braille", color="red", label="Heart Rate")
        plt.title("Heart Rate Trend - Last 24 Hours")
        plt.xlabel("Hour of Day")
        plt.ylabel("Beats per Minute")
        plt.plotsize(100, 15)
        plt.grid(True, True)

        # Add average line (plotext doesn't have axhline, so we'll add it to the title)
        if rates:
            avg_rate = sum(rates) / len(rates)
            plt.title(f"Heart Rate Trend - Last 24 Hours (Avg: {avg_rate:.1f} BPM)")

        plot_str = plt.build()
        return Panel(plot_str, title="Heart Rate Trend Graph", border_style="red")

    def create_zones_graph(self, zones):
        """Create zones distribution graph."""
        if not zones:
            return Panel("No zone data available", title="Zone Distribution", border_style="green")

        plt.clf()
        plt.theme("dark")

        names = list(zones.keys())
        values = list(zones.values())

        plt.bar(names, values, color=["blue", "green", "yellow", "orange", "red"])
        plt.title("Heart Rate Zone Distribution")
        plt.xlabel("Heart Rate Zone")
        plt.ylabel("Percentage of Time (%)")
        plt.plotsize(100, 12)
        plt.grid(False, True)

        plot_str = plt.build()
        return Panel(plot_str, title="Heart Rate Zones", border_style="green")

    def create_hourly_stats(self, hourly_data):
        """Create hourly statistics table."""
        from rich.table import Table

        table = Table(show_header=True, header_style="bold cyan", expand=False)
        table.add_column("Time Period", style="white")
        table.add_column("Avg HR", justify="right", style="red")
        table.add_column("Status", justify="center")

        if not hourly_data:
            table.add_row("No data", "-", "-")
        else:
            # Group into time periods
            periods = [
                ("Night (0-6h)", [d[1] for d in hourly_data if 0 <= d[0] <= 6]),
                ("Morning (7-12h)", [d[1] for d in hourly_data if 7 <= d[0] <= 12]),
                ("Afternoon (13-18h)", [d[1] for d in hourly_data if 13 <= d[0] <= 18]),
                ("Evening (19-23h)", [d[1] for d in hourly_data if 19 <= d[0] <= 23]),
            ]

            for period_name, period_rates in periods:
                if period_rates:
                    avg_hr = sum(period_rates) / len(period_rates)
                    status = "🟢" if 60 <= avg_hr <= 100 else "🟡" if avg_hr > 100 else "🔵"
                    table.add_row(period_name, f"{avg_hr:.0f} BPM", status)
                else:
                    table.add_row(period_name, "No data", "⚪")

        return Panel(table, title="Hourly Breakdown", border_style="cyan")

    def create_hrv_panel(self, hrv, trend_data):
        """Create HRV and trend panel."""
        from rich.table import Table

        table = Table(show_header=True, header_style="bold magenta", expand=False)
        table.add_column("Metric", style="white")
        table.add_column("Value", justify="right", style="yellow")
        table.add_column("Assessment", justify="center")

        # HRV data
        if hrv:
            hrv_status = "🟢 Good" if hrv > 30 else "🟡 Fair" if hrv > 20 else "🔴 Low"
            table.add_row("💓 HRV (24h)", f"{hrv:.1f} ms", hrv_status)
        else:
            table.add_row("💓 HRV (24h)", "No data", "⚪")

        # Trend data
        if trend_data:
            trend = trend_data.get("trend", "stable")
            change = trend_data.get("avg_change", 0)

            trend_symbols = {"increasing": "↗️", "decreasing": "↘️", "stable": "➡️"}
            trend_symbol = trend_symbols.get(trend, "❓")

            table.add_row("📈 7-Day Trend", f"{change:+.1f} BPM", f"{trend_symbol} {trend.title()}")

            percentage = trend_data.get("change_percentage", 0)
            perc_status = "🟢" if abs(percentage) < 5 else "🟡" if abs(percentage) < 10 else "🔴"
            table.add_row("📊 Change %", f"{percentage:+.1f}%", perc_status)
        else:
            table.add_row("📈 7-Day Trend", "No data", "⚪")
            table.add_row("📊 Change %", "No data", "⚪")

        return Panel(table, title="Heart Rate Variability & Trends", border_style="magenta")