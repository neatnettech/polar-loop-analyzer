from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class HeartRateSource(str, Enum):
    TIMED_24_7 = "TIMED_24_7"
    MANUAL = "MANUAL"
    UNKNOWN = "UNKNOWN"


class HeartRateSample(BaseModel):
    timestamp: datetime
    heart_rate: int = Field(gt=0, le=250)
    source: HeartRateSource
    device_id: str

    @classmethod
    def from_json_data(cls, data: dict, device_id: str, base_date: date) -> "HeartRateSample":
        seconds = data.get("secondsFromDayStart", 0)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        timestamp = datetime.combine(base_date, datetime.min.time()).replace(
            hour=hours, minute=minutes, second=secs
        )

        return cls(
            timestamp=timestamp,
            heart_rate=data["heartRate"],
            source=HeartRateSource(data.get("source", "UNKNOWN")),
            device_id=device_id
        )


class PPISample(BaseModel):
    timestamp: datetime
    pulse_length: int = Field(gt=0)  # milliseconds
    device_id: str

    @property
    def instantaneous_heart_rate(self) -> float:
        return 60000.0 / self.pulse_length if self.pulse_length > 0 else 0.0

    @classmethod
    def from_json_data(cls, data: dict, device_id: str) -> "PPISample":
        return cls(
            timestamp=datetime.fromisoformat(data["sampleDateTime"]),
            pulse_length=data["pulseLength"],
            device_id=device_id
        )


class ActivitySample(BaseModel):
    timestamp: datetime
    mets_value: float = Field(gt=0)
    date: date

    @property
    def calories_per_minute(self) -> float:
        # Assuming 70kg person for now
        return self.mets_value * 70 * 3.5 / 200

    @classmethod
    def from_json_data(cls, mets_value: float, index: int, base_date: date) -> "ActivitySample":
        # Each sample represents 1 minute
        hours = index // 60
        minutes = index % 60

        timestamp = datetime.combine(base_date, datetime.min.time()).replace(
            hour=hours, minute=minutes
        )

        return cls(
            timestamp=timestamp,
            mets_value=mets_value,
            date=base_date
        )


class Device(BaseModel):
    device_id: str
    user_id: Optional[int] = None
    name: Optional[str] = None


class DailySummary(BaseModel):
    date: date
    device_id: str
    avg_heart_rate: Optional[float] = None
    min_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    total_samples: int = 0
    avg_mets: Optional[float] = None
    total_calories: Optional[float] = None