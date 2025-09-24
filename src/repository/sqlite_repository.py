from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from src.repository.base import HeartRateRepository, PPIRepository, ActivityRepository, DeviceRepository
from src.domain.models import HeartRateSample, PPISample, ActivitySample, Device, HeartRateSource
from src.infrastructure.database import HeartRateDB, PPISampleDB, ActivitySampleDB, DeviceDB, Database


class SqliteHeartRateRepository(HeartRateRepository):
    def __init__(self, db: Database):
        self.db = db

    def add(self, sample: HeartRateSample) -> None:
        with self.db.get_session() as session:
            db_sample = HeartRateDB(
                timestamp=sample.timestamp,
                heart_rate=sample.heart_rate,
                source=sample.source.value,
                device_id=sample.device_id
            )
            session.add(db_sample)
            session.commit()

    def add_batch(self, samples: List[HeartRateSample]) -> None:
        with self.db.get_session() as session:
            for sample in samples:
                db_sample = HeartRateDB(
                    timestamp=sample.timestamp,
                    heart_rate=sample.heart_rate,
                    source=sample.source.value,
                    device_id=sample.device_id
                )
                session.add(db_sample)
            session.commit()

    def get_by_date_range(self, start: datetime, end: datetime, device_id: Optional[str] = None) -> List[HeartRateSample]:
        with self.db.get_session() as session:
            query = session.query(HeartRateDB).filter(
                HeartRateDB.timestamp >= start,
                HeartRateDB.timestamp <= end
            )
            if device_id:
                query = query.filter(HeartRateDB.device_id == device_id)

            results = query.order_by(HeartRateDB.timestamp).all()

            return [
                HeartRateSample(
                    timestamp=r.timestamp,
                    heart_rate=r.heart_rate,
                    source=HeartRateSource(r.source),
                    device_id=r.device_id
                )
                for r in results
            ]

    def get_latest(self, device_id: Optional[str] = None, limit: int = 1) -> List[HeartRateSample]:
        with self.db.get_session() as session:
            query = session.query(HeartRateDB)
            if device_id:
                query = query.filter(HeartRateDB.device_id == device_id)

            results = query.order_by(HeartRateDB.timestamp.desc()).limit(limit).all()

            return [
                HeartRateSample(
                    timestamp=r.timestamp,
                    heart_rate=r.heart_rate,
                    source=HeartRateSource(r.source),
                    device_id=r.device_id
                )
                for r in results
            ]

    def delete_by_date(self, target_date: date, device_id: Optional[str] = None) -> None:
        with self.db.get_session() as session:
            start = datetime.combine(target_date, datetime.min.time())
            end = datetime.combine(target_date, datetime.max.time())

            query = session.query(HeartRateDB).filter(
                HeartRateDB.timestamp >= start,
                HeartRateDB.timestamp <= end
            )
            if device_id:
                query = query.filter(HeartRateDB.device_id == device_id)

            query.delete()
            session.commit()


class SqlitePPIRepository(PPIRepository):
    def __init__(self, db: Database):
        self.db = db

    def add(self, sample: PPISample) -> None:
        with self.db.get_session() as session:
            db_sample = PPISampleDB(
                timestamp=sample.timestamp,
                pulse_length=sample.pulse_length,
                device_id=sample.device_id
            )
            session.add(db_sample)
            session.commit()

    def add_batch(self, samples: List[PPISample]) -> None:
        with self.db.get_session() as session:
            for sample in samples:
                db_sample = PPISampleDB(
                    timestamp=sample.timestamp,
                    pulse_length=sample.pulse_length,
                    device_id=sample.device_id
                )
                session.add(db_sample)
            session.commit()

    def get_by_date_range(self, start: datetime, end: datetime, device_id: Optional[str] = None) -> List[PPISample]:
        with self.db.get_session() as session:
            query = session.query(PPISampleDB).filter(
                PPISampleDB.timestamp >= start,
                PPISampleDB.timestamp <= end
            )
            if device_id:
                query = query.filter(PPISampleDB.device_id == device_id)

            results = query.order_by(PPISampleDB.timestamp).all()

            return [
                PPISample(
                    timestamp=r.timestamp,
                    pulse_length=r.pulse_length,
                    device_id=r.device_id
                )
                for r in results
            ]


class SqliteActivityRepository(ActivityRepository):
    def __init__(self, db: Database):
        self.db = db

    def add(self, sample: ActivitySample) -> None:
        with self.db.get_session() as session:
            db_sample = ActivitySampleDB(
                timestamp=sample.timestamp,
                mets_value=sample.mets_value,
                date=sample.date
            )
            session.add(db_sample)
            session.commit()

    def add_batch(self, samples: List[ActivitySample]) -> None:
        with self.db.get_session() as session:
            for sample in samples:
                db_sample = ActivitySampleDB(
                    timestamp=sample.timestamp,
                    mets_value=sample.mets_value,
                    date=sample.date
                )
                session.add(db_sample)
            session.commit()

    def get_by_date(self, target_date: date) -> List[ActivitySample]:
        with self.db.get_session() as session:
            results = session.query(ActivitySampleDB).filter(
                ActivitySampleDB.date == target_date
            ).order_by(ActivitySampleDB.timestamp).all()

            return [
                ActivitySample(
                    timestamp=r.timestamp,
                    mets_value=r.mets_value,
                    date=r.date
                )
                for r in results
            ]


class SqliteDeviceRepository(DeviceRepository):
    def __init__(self, db: Database):
        self.db = db

    def add(self, device: Device) -> None:
        with self.db.get_session() as session:
            existing = session.query(DeviceDB).filter(
                DeviceDB.device_id == device.device_id
            ).first()

            if not existing:
                db_device = DeviceDB(
                    device_id=device.device_id,
                    user_id=device.user_id,
                    name=device.name
                )
                session.add(db_device)
                session.commit()

    def get_by_device_id(self, device_id: str) -> Optional[Device]:
        with self.db.get_session() as session:
            result = session.query(DeviceDB).filter(
                DeviceDB.device_id == device_id
            ).first()

            if result:
                return Device(
                    device_id=result.device_id,
                    user_id=result.user_id,
                    name=result.name
                )
            return None

    def get_all(self) -> List[Device]:
        with self.db.get_session() as session:
            results = session.query(DeviceDB).all()

            return [
                Device(
                    device_id=r.device_id,
                    user_id=r.user_id,
                    name=r.name
                )
                for r in results
            ]