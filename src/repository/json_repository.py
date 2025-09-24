import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, date
from src.domain.models import HeartRateSample, PPISample, ActivitySample, Device


class JsonDataReader:
    def __init__(self, data_directory: Path):
        self.data_directory = data_directory

    def read_heart_rate_data(self) -> List[HeartRateSample]:
        samples = []
        hr_files = list(self.data_directory.glob("247ohr_*.json"))

        for file_path in hr_files:
            with open(file_path, 'r') as f:
                data = json.load(f)

            for device_day in data.get("deviceDays", []):
                device_id = device_day["deviceId"]
                base_date = date.fromisoformat(device_day["date"])

                for sample_data in device_day.get("samples", []):
                    sample = HeartRateSample.from_json_data(sample_data, device_id, base_date)
                    samples.append(sample)

        return samples

    def read_ppi_data(self) -> List[PPISample]:
        samples = []
        ppi_files = list(self.data_directory.glob("ppi_samples_*.json"))

        for file_path in ppi_files:
            with open(file_path, 'r') as f:
                data = json.load(f)

            for day_data in data:
                for device_data in day_data.get("devicePpiSamplesList", []):
                    device_id = device_data["deviceId"]

                    for sample_data in device_data.get("ppiSamples", []):
                        sample = PPISample.from_json_data(sample_data, device_id)
                        samples.append(sample)

        return samples

    def read_activity_data(self) -> List[ActivitySample]:
        samples = []
        activity_files = list(self.data_directory.glob("activity-*.json"))

        for file_path in activity_files:
            with open(file_path, 'r') as f:
                data = json.load(f)

            base_date = date.fromisoformat(data["date"])
            mets_samples = data.get("samples", {}).get("mets", [])

            for index, mets_data in enumerate(mets_samples):
                sample = ActivitySample.from_json_data(
                    mets_data["value"], index, base_date
                )
                samples.append(sample)

        return samples

    def read_devices(self) -> List[Device]:
        devices = set()

        # Extract from heart rate data
        hr_files = list(self.data_directory.glob("247ohr_*.json"))
        for file_path in hr_files:
            with open(file_path, 'r') as f:
                data = json.load(f)
            for device_day in data.get("deviceDays", []):
                device_id = device_day["deviceId"]
                user_id = device_day.get("userId")
                devices.add((device_id, user_id))

        # Extract from PPI data
        ppi_files = list(self.data_directory.glob("ppi_samples_*.json"))
        for file_path in ppi_files:
            with open(file_path, 'r') as f:
                data = json.load(f)
            for day_data in data:
                for device_data in day_data.get("devicePpiSamplesList", []):
                    device_id = device_data["deviceId"]
                    devices.add((device_id, None))

        return [
            Device(device_id=dev_id, user_id=user_id)
            for dev_id, user_id in devices
        ]

    def read_all_data(self) -> Dict[str, Any]:
        return {
            "heart_rates": self.read_heart_rate_data(),
            "ppi_samples": self.read_ppi_data(),
            "activities": self.read_activity_data(),
            "devices": self.read_devices()
        }