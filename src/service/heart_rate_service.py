from typing import List, Optional, Dict, Tuple, Any
from datetime import datetime, date, timedelta
from statistics import mean, median, stdev
from src.repository.sqlite_repository import SqliteHeartRateRepository, SqlitePPIRepository
from src.domain.models import HeartRateSample, PPISample, DailySummary
from src.domain.value_objects import HeartRateZones, TimeRange
from src.infrastructure.database import Database


class HeartRateService:
    def __init__(self, database: Database):
        self.hr_repo = SqliteHeartRateRepository(database)
        self.ppi_repo = SqlitePPIRepository(database)
        self.zones = HeartRateZones()

    def get_current_stats(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        latest_samples = self.hr_repo.get_latest(device_id, limit=60)  # Last 60 samples

        if not latest_samples:
            return {
                "current_hr": None,
                "avg_hr": None,
                "min_hr": None,
                "max_hr": None,
                "trend": "stable",
                "zone": None
            }

        heart_rates = [s.heart_rate for s in latest_samples]
        current_hr = latest_samples[0].heart_rate
        current_zone = self.zones.get_zone(current_hr)

        # Calculate trend
        if len(heart_rates) >= 10:
            recent_avg = mean(heart_rates[:5])
            older_avg = mean(heart_rates[5:10])
            if recent_avg > older_avg + 3:
                trend = "increasing"
            elif recent_avg < older_avg - 3:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "current_hr": current_hr,
            "avg_hr": round(mean(heart_rates), 1),
            "min_hr": min(heart_rates),
            "max_hr": max(heart_rates),
            "trend": trend,
            "zone": current_zone.name if current_zone else None,
            "zone_color": current_zone.color if current_zone else None
        }

    def get_hourly_averages(self, target_date: date, device_id: Optional[str] = None) -> List[Tuple[int, float]]:
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        samples = self.hr_repo.get_by_date_range(start, end, device_id)

        hourly_data = {}
        for sample in samples:
            hour = sample.timestamp.hour
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(sample.heart_rate)

        return [(hour, mean(rates)) for hour, rates in sorted(hourly_data.items())]

    def get_zone_distribution(self, start: datetime, end: datetime, device_id: Optional[str] = None) -> Dict[str, float]:
        samples = self.hr_repo.get_by_date_range(start, end, device_id)

        zone_counts = {zone.name: 0 for zone in self.zones.zones}
        total = len(samples)

        if total == 0:
            return {name: 0.0 for name in zone_counts}

        for sample in samples:
            zone = self.zones.get_zone(sample.heart_rate)
            if zone:
                zone_counts[zone.name] += 1

        return {name: (count / total) * 100 for name, count in zone_counts.items()}

    def calculate_hrv(self, start: datetime, end: datetime, device_id: Optional[str] = None) -> Optional[float]:
        ppi_samples = self.ppi_repo.get_by_date_range(start, end, device_id)

        if len(ppi_samples) < 2:
            return None

        intervals = [s.pulse_length for s in ppi_samples]
        differences = [abs(intervals[i+1] - intervals[i]) for i in range(len(intervals) - 1)]

        if differences:
            # RMSSD calculation
            squared_diffs = [d ** 2 for d in differences]
            return (sum(squared_diffs) / len(squared_diffs)) ** 0.5

        return None

    def get_daily_summary(self, target_date: date, device_id: Optional[str] = None) -> DailySummary:
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        samples = self.hr_repo.get_by_date_range(start, end, device_id)

        if samples:
            heart_rates = [s.heart_rate for s in samples]
            summary = DailySummary(
                date=target_date,
                device_id=device_id or "unknown",
                avg_heart_rate=mean(heart_rates),
                min_heart_rate=min(heart_rates),
                max_heart_rate=max(heart_rates),
                total_samples=len(samples)
            )
        else:
            summary = DailySummary(
                date=target_date,
                device_id=device_id or "unknown",
                total_samples=0
            )

        return summary