from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Label
from textual.reactive import reactive
from textual.timer import Timer
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from typing import Optional


class DashboardView(Container):
    """Main dashboard view."""

    def __init__(self, facade, **kwargs):
        super().__init__(**kwargs)
        self.facade = facade
        self.timer: Optional[Timer] = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the dashboard."""
        yield Vertical(
            Label("📊 Dashboard - Today's Summary", id="title"),
            Static(id="current_hr"),
            Horizontal(
                Static(id="hr_zones_table"),
                Static(id="activity_summary"),
                classes="stats-row"
            ),
            Static(id="weekly_overview"),
            Static(id="device_info"),
            classes="dashboard"
        )

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.update_dashboard()
        # Update every 5 seconds
        self.timer = self.set_interval(5, self.update_dashboard)

    def update_dashboard(self) -> None:
        """Update all dashboard components."""
        try:
            data = self.facade.get_dashboard_data()

            # Update current HR summary
            hr_stats_widget = self.query_one("#current_hr", Static)
            hr_stats_widget.update(self.create_current_hr_panel(data["current_hr"]))

            # Update HR zones table
            zones_widget = self.query_one("#hr_zones_table", Static)
            zones_widget.update(self.create_zones_table(data["zone_distribution"]))

            # Update activity summary
            activity_widget = self.query_one("#activity_summary", Static)
            activity_widget.update(self.create_activity_summary(data["activity"]))

            # Update weekly overview
            weekly_widget = self.query_one("#weekly_overview", Static)
            weekly_widget.update(self.create_weekly_table(data["weekly"]))

            # Update device info
            device_widget = self.query_one("#device_info", Static)
            device_widget.update(self.create_device_panel(data))

        except Exception as e:
            self.query_one("#current_hr", Static).update(
                Panel(f"Error updating dashboard: {str(e)}", title="Error", border_style="red")
            )

    def create_current_hr_panel(self, hr_data):
        """Create current heart rate stats panel."""
        if not hr_data or hr_data.get("current_hr") is None:
            return Panel("No recent heart rate data", title="Heart Rate Summary", border_style="yellow")

        zone = hr_data.get('zone', 'N/A')
        zone_color = hr_data.get('zone_color', 'white')
        trend = hr_data.get('trend', 'N/A')

        content = f"""❤️  Current: [bold red]{hr_data.get('current_hr', 'N/A')} BPM[/bold red]   |   📊 Avg: {hr_data.get('avg_hr', 'N/A')} BPM   |   📉📈 Min/Max: {hr_data.get('min_hr', 'N/A')}/{hr_data.get('max_hr', 'N/A')} BPM   |   🎯 Zone: [{zone_color}]{zone}[/{zone_color}]   |   📍 Trend: {trend}"""
        return Panel(content.strip(), title="Heart Rate Summary", border_style="yellow")

    def create_zones_table(self, zones):
        """Create heart rate zones table."""
        table = Table(show_header=True, header_style="bold cyan", expand=False)
        table.add_column("Zone", style="white")
        table.add_column("Time %", justify="right", style="yellow")
        table.add_column("Status", justify="center")

        if not zones:
            table.add_row("No zone data", "-", "-")
        else:
            zone_colors = {
                "Rest": "blue",
                "Light": "green",
                "Moderate": "yellow",
                "Hard": "orange1",
                "Maximum": "red"
            }

            for zone, percentage in zones.items():
                color = zone_colors.get(zone, "white")
                status = "●" if percentage > 5 else "○"
                table.add_row(
                    f"[{color}]{zone}[/{color}]",
                    f"{percentage:.1f}%",
                    f"[{color}]{status}[/{color}]"
                )

        return Panel(table, title="Heart Rate Zones", border_style="cyan")

    def create_activity_summary(self, activity_data):
        """Create activity summary table."""
        table = Table(show_header=True, header_style="bold green", expand=False)
        table.add_column("Metric", style="white")
        table.add_column("Value", justify="right", style="yellow")

        if not activity_data:
            table.add_row("No activity data", "-")
        else:
            table.add_row("🔥 Calories", f"{activity_data.get('total_calories', 0):.1f} kcal")
            table.add_row("⚡ Avg METs", f"{activity_data.get('avg_mets', 0):.2f}")
            table.add_row("🏃 Active Time", f"{activity_data.get('active_minutes', 0)} min")
            table.add_row("🪑 Sedentary", f"{activity_data.get('sedentary_minutes', 0)} min")
            table.add_row("📊 Activity %", f"{activity_data.get('activity_percentage', 0):.1f}%")

        return Panel(table, title="Activity Today", border_style="green")

    def create_weekly_table(self, weekly_data):
        """Create weekly overview table."""
        table = Table(show_header=True, header_style="bold magenta", expand=True)
        table.add_column("Day", style="white")
        table.add_column("Avg HR", justify="right", style="red")
        table.add_column("Calories", justify="right", style="yellow")
        table.add_column("Samples", justify="right", style="cyan")
        table.add_column("Status", justify="center")

        if not weekly_data:
            table.add_row("No weekly data", "-", "-", "-", "-")
        else:
            for day in weekly_data[-7:]:  # Last 7 days
                avg_hr = day.get('avg_heart_rate')
                status = "✓" if avg_hr else "○"
                hr_display = f"{avg_hr:.0f} BPM" if avg_hr else "No data"

                table.add_row(
                    day.get('day_name', 'Unknown'),
                    hr_display,
                    f"{day.get('total_calories', 0):.0f} kcal",
                    str(day.get('sample_count', 0)),
                    status
                )

        return Panel(table, title="Weekly Overview (Last 7 Days)", border_style="magenta")

    def create_device_panel(self, data):
        """Create device and system info panel."""
        devices = self.facade.get_devices()
        hrv = data.get('hrv')
        trend = data.get('trend', {})

        table = Table(show_header=True, header_style="bold blue", expand=True)
        table.add_column("Info Type", style="white")
        table.add_column("Value", justify="right", style="yellow")

        table.add_row("📱 Active Device", devices[0] if devices else "None")
        table.add_row("💓 HRV (24h)", f"{hrv:.1f} ms" if hrv else "No data")

        trend_symbol = {"increasing": "↗️", "decreasing": "↘️", "stable": "➡️"}.get(
            trend.get("trend", "stable"), "❓"
        )
        table.add_row("📈 7-Day Trend", f"{trend_symbol} {trend.get('trend', 'N/A').title()}")
        table.add_row("🔄 Last Update", "Just now")

        return Panel(table, title="Device & Status", border_style="blue")