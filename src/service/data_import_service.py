from pathlib import Path
from typing import Dict, Any
from src.repository.json_repository import JsonDataReader
from src.repository.sqlite_repository import (
    SqliteHeartRateRepository,
    SqlitePPIRepository,
    SqliteActivityRepository,
    SqliteDeviceRepository
)
from src.infrastructure.database import Database


class DataImportService:
    def __init__(self, database: Database, data_directory: Path):
        self.json_reader = JsonDataReader(data_directory)
        self.hr_repo = SqliteHeartRateRepository(database)
        self.ppi_repo = SqlitePPIRepository(database)
        self.activity_repo = SqliteActivityRepository(database)
        self.device_repo = SqliteDeviceRepository(database)

    def import_all_data(self) -> Dict[str, int]:
        stats = {
            "devices": 0,
            "heart_rate_samples": 0,
            "ppi_samples": 0,
            "activity_samples": 0
        }

        # Import devices first
        devices = self.json_reader.read_devices()
        for device in devices:
            self.device_repo.add(device)
        stats["devices"] = len(devices)

        # Import heart rate data
        hr_samples = self.json_reader.read_heart_rate_data()
        if hr_samples:
            self.hr_repo.add_batch(hr_samples)
        stats["heart_rate_samples"] = len(hr_samples)

        # Import PPI data
        ppi_samples = self.json_reader.read_ppi_data()
        if ppi_samples:
            self.ppi_repo.add_batch(ppi_samples)
        stats["ppi_samples"] = len(ppi_samples)

        # Import activity data
        activity_samples = self.json_reader.read_activity_data()
        if activity_samples:
            self.activity_repo.add_batch(activity_samples)
        stats["activity_samples"] = len(activity_samples)

        return stats

    def clear_all_data(self):
        # This would typically include methods to clear existing data
        # Implementation depends on specific requirements
        pass