from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from statistics import mean, median
from src.repository.sqlite_repository import SqliteActivityRepository, SqliteHeartRateRepository
from src.infrastructure.database import Database


class StatisticsService:
    def __init__(self, database: Database):
        self.activity_repo = SqliteActivityRepository(database)
        self.hr_repo = SqliteHeartRateRepository(database)

    def get_activity_stats(self, target_date: date) -> Dict[str, Any]:
        samples = self.activity_repo.get_by_date(target_date)

        if not samples:
            return {
                "total_calories": 0,
                "avg_mets": 0,
                "active_minutes": 0,
                "sedentary_minutes": 0
            }

        mets_values = [s.mets_value for s in samples]
        calories = [s.calories_per_minute for s in samples]

        # Count active vs sedentary minutes (MET > 1.5 is considered active)
        active_minutes = sum(1 for mets in mets_values if mets > 1.5)
        sedentary_minutes = len(mets_values) - active_minutes

        return {
            "total_calories": round(sum(calories), 1),
            "avg_mets": round(mean(mets_values), 2),
            "active_minutes": active_minutes,
            "sedentary_minutes": sedentary_minutes,
            "max_mets": round(max(mets_values), 2),
            "activity_percentage": round((active_minutes / len(mets_values)) * 100, 1) if mets_values else 0
        }

    def get_weekly_comparison(self, end_date: date, device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        weekly_data = []

        for i in range(7):
            current_date = end_date - timedelta(days=i)
            start = datetime.combine(current_date, datetime.min.time())
            end = datetime.combine(current_date, datetime.max.time())

            hr_samples = self.hr_repo.get_by_date_range(start, end, device_id)
            activity_samples = self.activity_repo.get_by_date(current_date)

            hr_avg = mean([s.heart_rate for s in hr_samples]) if hr_samples else None
            calories = sum([s.calories_per_minute for s in activity_samples]) if activity_samples else 0

            weekly_data.append({
                "date": current_date.isoformat(),
                "day_name": current_date.strftime("%A"),
                "avg_heart_rate": round(hr_avg, 1) if hr_avg else None,
                "total_calories": round(calories, 1),
                "sample_count": len(hr_samples)
            })

        return list(reversed(weekly_data))

    def get_trend_analysis(self, start_date: date, end_date: date, device_id: Optional[str] = None) -> Dict[str, Any]:
        daily_averages = []
        current = start_date

        while current <= end_date:
            start = datetime.combine(current, datetime.min.time())
            end = datetime.combine(current, datetime.max.time())

            samples = self.hr_repo.get_by_date_range(start, end, device_id)
            if samples:
                daily_avg = mean([s.heart_rate for s in samples])
                daily_averages.append(daily_avg)

            current += timedelta(days=1)

        if len(daily_averages) < 2:
            return {
                "trend": "insufficient_data",
                "change_percentage": 0,
                "avg_change": 0
            }

        # Simple linear trend
        first_half = daily_averages[:len(daily_averages)//2]
        second_half = daily_averages[len(daily_averages)//2:]

        first_avg = mean(first_half) if first_half else 0
        second_avg = mean(second_half) if second_half else 0

        if first_avg > 0:
            change_percentage = ((second_avg - first_avg) / first_avg) * 100
        else:
            change_percentage = 0

        if second_avg > first_avg + 2:
            trend = "increasing"
        elif second_avg < first_avg - 2:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "change_percentage": round(change_percentage, 1),
            "avg_change": round(second_avg - first_avg, 1),
            "period_days": (end_date - start_date).days + 1
        }