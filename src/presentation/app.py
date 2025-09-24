from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane, Static, Label
from textual.containers import Container
from textual.binding import Binding
from src.presentation.views.dashboard_view import DashboardView
from src.presentation.views.heart_rate_view import HeartRateView
from src.facade import PolarAnalyzerFacade
from rich.panel import Panel


class PolarAnalyzerApp(App):
    """Main TUI application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $primary;
        height: 1;
        margin: 0 0 1 0;
    }

    .dashboard {
        height: 100%;
        padding: 1;
        overflow-y: auto;
    }

    #current_hr {
        height: 3;
        margin-bottom: 1;
        width: 100%;
    }

    .stats-row {
        height: 12;
        width: 100%;
        layout: horizontal;
        margin-bottom: 1;
    }

    #hr_zones_table {
        width: 50%;
        margin-right: 1;
    }

    #activity_summary {
        width: 50%;
    }

    #weekly_overview {
        height: 11;
        margin-bottom: 1;
        width: 100%;
    }

    #device_info {
        height: 8;
        width: 100%;
    }

    .heart-rate-view {
        height: 100%;
        padding: 1;
        overflow-y: auto;
    }

    #hr_title {
        text-align: center;
        text-style: bold;
        color: red;
        height: 1;
        margin-bottom: 1;
    }

    #hr_current_detailed {
        height: 6;
        margin-bottom: 1;
        width: 100%;
    }

    #hr_trend_graph {
        height: 18;
        margin-bottom: 1;
        width: 100%;
    }

    #hr_zones_graph {
        height: 15;
        margin-bottom: 1;
        width: 100%;
    }

    .hr-stats-row {
        height: 12;
        width: 100%;
        layout: horizontal;
    }

    #hr_hourly_stats {
        width: 50%;
        margin-right: 1;
    }

    #hr_variability {
        width: 50%;
    }

    TabPane {
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def __init__(self):
        super().__init__()
        self.facade = PolarAnalyzerFacade()
        self.dark = True

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header(show_clock=True)

        with TabbedContent():
            with TabPane("Dashboard", id="dashboard"):
                yield DashboardView(self.facade)

            with TabPane("Heart Rate", id="heart_rate"):
                yield HeartRateView(self.facade)

            with TabPane("Activity", id="activity"):
                yield Container(
                    Static(id="activity_graph", classes="graph"),
                    Static(id="activity_detailed", classes="stats"),
                )

            with TabPane("Settings", id="settings"):
                yield Container(
                    Static(self.create_settings_panel(), id="settings_content"),
                )

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the application."""
        try:
            # Import data (incremental by default)
            stats = self.facade.initialize_data()

            # Select first device if available
            devices = self.facade.get_devices()
            if devices:
                self.facade.set_device(devices[0])

            # Show import stats
            if stats['new_files'] > 0:
                self.notify(
                    f"Processed {stats['new_files']} new files: "
                    f"{stats['heart_rate_samples']} HR samples, "
                    f"{stats['activity_samples']} activity samples. "
                    f"Skipped {stats['skipped_files']} existing files.",
                    timeout=5
                )
            else:
                self.notify(
                    f"All {stats['total_files']} files already imported. "
                    f"Add new files to loop_data/ and refresh.",
                    timeout=3
                )

            if stats['errors']:
                self.notify(
                    f"Import errors: {len(stats['errors'])} files failed",
                    severity="warning"
                )

        except Exception as e:
            self.notify(f"Error initializing: {str(e)}", severity="error")

    def action_refresh(self) -> None:
        """Refresh the dashboard and check for new files."""
        try:
            # Check for new files and import them
            new_files = self.facade.check_for_new_files()
            if new_files:
                stats = self.facade.initialize_data()
                if stats['new_files'] > 0:
                    self.notify(
                        f"Imported {stats['new_files']} new files: "
                        f"{stats['heart_rate_samples']} HR, "
                        f"{stats['activity_samples']} activity samples",
                        timeout=4
                    )
                else:
                    self.notify("No new data to import", timeout=2)

            # Refresh dashboard
            dashboard = self.query_one(DashboardView)
            dashboard.update_dashboard()

            if not new_files:
                self.notify("Dashboard refreshed", timeout=2)

        except Exception as e:
            self.notify(f"Refresh error: {str(e)}", severity="error")

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark
        self.notify(f"Dark mode: {'ON' if self.dark else 'OFF'}", timeout=2)

    def create_settings_panel(self) -> Panel:
        """Create settings panel."""
        devices = self.facade.get_devices()
        device_list = "\n".join([f"• {d}" for d in devices]) if devices else "No devices found"

        content = f"""
[bold]Application Settings[/bold]

[cyan]Connected Devices:[/cyan]
{device_list}

[cyan]Database:[/cyan]
• Location: data.db
• Status: Connected

[cyan]Data Directory:[/cyan]
• Path: loop_data/

[yellow]Keyboard Shortcuts:[/yellow]
• q - Quit application
• r - Refresh dashboard
• d - Toggle dark mode
• Tab - Switch between tabs
        """
        return Panel(content.strip(), title="Settings", border_style="blue")

    def on_unmount(self) -> None:
        """Clean up when app closes."""
        self.facade.cleanup()