import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import date
from src.repository.json_repository import JsonDataReader
from src.repository.file_import_repository import FileImportRepository
from src.repository.sqlite_repository import (
    SqliteHeartRateRepository,
    SqlitePPIRepository,
    SqliteActivityRepository,
    SqliteDeviceRepository
)
from src.domain.models import HeartRateSample, PPISample, ActivitySample, Device
from src.infrastructure.database import Database


class DataImportService:
    def __init__(self, database: Database, data_directory: Path):
        self.data_directory = data_directory
        self.json_reader = JsonDataReader(data_directory)
        self.file_import_repo = FileImportRepository(database)
        self.hr_repo = SqliteHeartRateRepository(database)
        self.ppi_repo = SqlitePPIRepository(database)
        self.activity_repo = SqliteActivityRepository(database)
        self.device_repo = SqliteDeviceRepository(database)

    def import_all_data(self, force_reimport: bool = False) -> Dict[str, Any]:
        """Import all data with incremental import support."""
        stats = {
            "total_files": 0,
            "new_files": 0,
            "skipped_files": 0,
            "devices": 0,
            "heart_rate_samples": 0,
            "ppi_samples": 0,
            "activity_samples": 0,
            "errors": []
        }

        # Get all JSON files
        all_files = list(self.data_directory.glob("*.json"))
        stats["total_files"] = len(all_files)

        if force_reimport:
            new_files = all_files
        else:
            # Only process new files
            new_files = self.file_import_repo.get_new_files(self.data_directory)

        stats["new_files"] = len(new_files)
        stats["skipped_files"] = len(all_files) - len(new_files)

        if not new_files:
            return stats

        # Process each new file
        for file_path in new_files:
            try:
                file_stats = self.import_single_file(file_path)

                # Accumulate stats
                stats["devices"] += file_stats.get("devices", 0)
                stats["heart_rate_samples"] += file_stats.get("heart_rate_samples", 0)
                stats["ppi_samples"] += file_stats.get("ppi_samples", 0)
                stats["activity_samples"] += file_stats.get("activity_samples", 0)

            except Exception as e:
                error_msg = f"Failed to import {file_path.name}: {str(e)}"
                stats["errors"].append(error_msg)
                self.file_import_repo.record_import_completion(
                    file_path.name, 0, 'failed', error_msg
                )

        return stats

    def import_single_file(self, file_path: Path) -> Dict[str, int]:
        """Import a single file and track it."""
        file_stats = {
            "devices": 0,
            "heart_rate_samples": 0,
            "ppi_samples": 0,
            "activity_samples": 0
        }

        # Record import start
        import_record = self.file_import_repo.record_import_start(file_path)
        filename = file_path.name

        try:
            # Determine file type and process accordingly
            if '247ohr' in filename:
                samples = self._import_heart_rate_file(file_path)
                file_stats["heart_rate_samples"] = len(samples)

            elif 'activity' in filename:
                samples = self._import_activity_file(file_path)
                file_stats["activity_samples"] = len(samples)

            elif 'ppi_samples' in filename:
                samples = self._import_ppi_file(file_path)
                file_stats["ppi_samples"] = len(samples)

            elif any(keyword in filename for keyword in ['account', 'products-devices']):
                devices = self._import_devices_from_file(file_path)
                file_stats["devices"] = len(devices)

            # Record successful completion
            total_records = sum(file_stats.values())
            self.file_import_repo.record_import_completion(
                filename, total_records, 'completed'
            )

        except Exception as e:
            # Record failure
            self.file_import_repo.record_import_completion(
                filename, 0, 'failed', str(e)
            )
            raise

        return file_stats

    def _import_heart_rate_file(self, file_path: Path) -> List[HeartRateSample]:
        """Import heart rate data from a specific file."""
        with open(file_path, 'r') as f:
            data = json.load(f)

        samples = []
        for device_day in data.get("deviceDays", []):
            device_id = device_day["deviceId"]
            base_date = date.fromisoformat(device_day["date"])

            # Ensure device exists
            device = Device(device_id=device_id, user_id=device_day.get("userId"))
            self.device_repo.add(device)

            for sample_data in device_day.get("samples", []):
                sample = HeartRateSample.from_json_data(sample_data, device_id, base_date)
                samples.append(sample)

        if samples:
            self.hr_repo.add_batch(samples)

        return samples

    def _import_activity_file(self, file_path: Path) -> List[ActivitySample]:
        """Import activity data from a specific file."""
        with open(file_path, 'r') as f:
            data = json.load(f)

        base_date = date.fromisoformat(data["date"])
        mets_samples = data.get("samples", {}).get("mets", [])

        samples = []
        for index, mets_data in enumerate(mets_samples):
            sample = ActivitySample.from_json_data(
                mets_data["value"], index, base_date
            )
            samples.append(sample)

        if samples:
            self.activity_repo.add_batch(samples)

        return samples

    def _import_ppi_file(self, file_path: Path) -> List[PPISample]:
        """Import PPI data from a specific file."""
        with open(file_path, 'r') as f:
            data = json.load(f)

        samples = []
        for day_data in data:
            for device_data in day_data.get("devicePpiSamplesList", []):
                device_id = device_data["deviceId"]

                # Ensure device exists
                device = Device(device_id=device_id)
                self.device_repo.add(device)

                for sample_data in device_data.get("ppiSamples", []):
                    sample = PPISample.from_json_data(sample_data, device_id)
                    samples.append(sample)

        if samples:
            self.ppi_repo.add_batch(samples)

        return samples

    def _import_devices_from_file(self, file_path: Path) -> List[Device]:
        """Import device info from various files."""
        devices = []

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Handle different file types
            if 'products-devices' in file_path.name:
                # Extract device info from products-devices file
                for item in data if isinstance(data, list) else [data]:
                    if 'deviceId' in item:
                        device = Device(
                            device_id=item['deviceId'],
                            name=item.get('name', item.get('productName'))
                        )
                        devices.append(device)
                        self.device_repo.add(device)

            elif 'account' in file_path.name:
                # Extract user info that might reference devices
                if 'userId' in data:
                    # This is handled when processing actual data files
                    pass

        except Exception as e:
            # Non-critical error for device files
            pass

        return devices

    def get_import_history(self) -> List[dict]:
        """Get history of file imports."""
        return self.file_import_repo.get_import_history()

    def get_import_stats(self) -> dict:
        """Get statistics about imports."""
        return self.file_import_repo.get_import_stats()

    def force_reimport_file(self, filename: str) -> Dict[str, Any]:
        """Force reimport of a specific file."""
        file_path = self.data_directory / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File {filename} not found")

        # Remove existing import record
        self.file_import_repo.remove_import_record(filename)

        # Import the file
        return self.import_single_file(file_path)

    def clear_all_data(self):
        """Clear all import tracking (for development/testing)."""
        # This would typically include methods to clear existing data
        # Implementation depends on specific requirements
        pass