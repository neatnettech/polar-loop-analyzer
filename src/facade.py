from typing import Dict, Any, Optional, List, Tuple
from datetime import date, datetime
from pathlib import Path
from src.infrastructure.database import Database
from src.infrastructure.config import AppConfig
from src.service.data_import_service import DataImportService
from src.service.heart_rate_service import HeartRateService
from src.service.statistics_service import StatisticsService
from src.repository.sqlite_repository import SqliteDeviceRepository


class PolarAnalyzerFacade:
    """
    Facade pattern implementation providing a simplified interface
    to the complex subsystem of services and repositories.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or AppConfig()
        self.db = Database(self.config.database_path)

        # Initialize services
        self.import_service = DataImportService(self.db, self.config.data_directory)
        self.hr_service = HeartRateService(self.db)
        self.stats_service = StatisticsService(self.db)
        self.device_repo = SqliteDeviceRepository(self.db)

        self._current_device_id = None

    def initialize_data(self) -> Dict[str, int]:
        """Import all data from JSON files into SQLite database."""
        return self.import_service.import_all_data()

    def set_device(self, device_id: str) -> bool:
        """Set the current device for operations."""
        device = self.device_repo.get_by_device_id(device_id)
        if device:
            self._current_device_id = device_id
            return True
        return False

    def get_devices(self) -> List[str]:
        """Get list of available device IDs."""
        devices = self.device_repo.get_all()
        return [d.device_id for d in devices]

    def get_current_heart_rate(self) -> Dict[str, Any]:
        """Get current heart rate statistics."""
        return self.hr_service.get_current_stats(self._current_device_id)

    def get_heart_rate_graph_data(self, date: Optional[date] = None) -> List[Tuple[int, float]]:
        """Get hourly heart rate data for graphing."""
        target_date = date or datetime.now().date()
        return self.hr_service.get_hourly_averages(target_date, self._current_device_id)

    def get_zone_distribution(self, hours: int = 24) -> Dict[str, float]:
        """Get heart rate zone distribution for the last N hours."""
        end = datetime.now()
        start = end - timedelta(hours=hours)
        return self.hr_service.get_zone_distribution(start, end, self._current_device_id)

    def get_activity_summary(self, date: Optional[date] = None) -> Dict[str, Any]:
        """Get activity summary for a specific date."""
        target_date = date or datetime.now().date()
        return self.stats_service.get_activity_stats(target_date)

    def get_weekly_overview(self) -> List[Dict[str, Any]]:
        """Get weekly comparison data."""
        today = datetime.now().date()
        return self.stats_service.get_weekly_comparison(today, self._current_device_id)

    def get_hrv(self, hours: int = 24) -> Optional[float]:
        """Get heart rate variability for the last N hours."""
        end = datetime.now()
        start = end - timedelta(hours=hours)
        return self.hr_service.calculate_hrv(start, end, self._current_device_id)

    def get_trend_info(self, days: int = 7) -> Dict[str, Any]:
        """Get trend analysis for the last N days."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        return self.stats_service.get_trend_analysis(start_date, end_date, self._current_device_id)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all data needed for the dashboard view."""
        return {
            "current_hr": self.get_current_heart_rate(),
            "hourly_data": self.get_heart_rate_graph_data(),
            "zone_distribution": self.get_zone_distribution(),
            "activity": self.get_activity_summary(),
            "weekly": self.get_weekly_overview(),
            "hrv": self.get_hrv(),
            "trend": self.get_trend_info()
        }

    def cleanup(self):
        """Clean up resources."""
        self.db.close()


from datetime import timedelta