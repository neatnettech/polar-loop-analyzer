from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta


@dataclass(frozen=True)
class HeartRateZone:
    name: str
    min_hr: int
    max_hr: int
    color: str

    def contains(self, heart_rate: int) -> bool:
        return self.min_hr <= heart_rate <= self.max_hr


class HeartRateZones:
    def __init__(self, max_hr: int = 190):
        self.zones = [
            HeartRateZone("Rest", 0, int(max_hr * 0.5), "blue"),
            HeartRateZone("Light", int(max_hr * 0.5), int(max_hr * 0.6), "green"),
            HeartRateZone("Moderate", int(max_hr * 0.6), int(max_hr * 0.7), "yellow"),
            HeartRateZone("Hard", int(max_hr * 0.7), int(max_hr * 0.85), "orange"),
            HeartRateZone("Maximum", int(max_hr * 0.85), max_hr, "red")
        ]

    def get_zone(self, heart_rate: int) -> Optional[HeartRateZone]:
        for zone in self.zones:
            if zone.contains(heart_rate):
                return zone
        return None


@dataclass(frozen=True)
class TimeRange:
    start: datetime
    end: datetime

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    def contains(self, timestamp: datetime) -> bool:
        return self.start <= timestamp <= self.end

    def overlaps(self, other: "TimeRange") -> bool:
        return not (self.end < other.start or other.end < self.start)