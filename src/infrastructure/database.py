from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from typing import Optional
from pathlib import Path

Base = declarative_base()


class DeviceDB(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    device_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=True)
    name = Column(String, nullable=True)

    heart_rates = relationship("HeartRateDB", back_populates="device", cascade="all, delete-orphan")
    ppi_samples = relationship("PPISampleDB", back_populates="device", cascade="all, delete-orphan")


class HeartRateDB(Base):
    __tablename__ = "heart_rates"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    heart_rate = Column(Integer, nullable=False)
    source = Column(String, nullable=False)
    device_id = Column(String, ForeignKey("devices.device_id"), nullable=False)

    device = relationship("DeviceDB", back_populates="heart_rates")


class PPISampleDB(Base):
    __tablename__ = "ppi_samples"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    pulse_length = Column(Integer, nullable=False)
    device_id = Column(String, ForeignKey("devices.device_id"), nullable=False)

    device = relationship("DeviceDB", back_populates="ppi_samples")


class ActivitySampleDB(Base):
    __tablename__ = "activity_samples"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    mets_value = Column(Float, nullable=False)
    date = Column(Date, nullable=False, index=True)


class DailySummaryDB(Base):
    __tablename__ = "daily_summaries"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    device_id = Column(String, ForeignKey("devices.device_id"), nullable=False)
    avg_heart_rate = Column(Float, nullable=True)
    min_heart_rate = Column(Integer, nullable=True)
    max_heart_rate = Column(Integer, nullable=True)
    total_samples = Column(Integer, default=0)
    avg_mets = Column(Float, nullable=True)
    total_calories = Column(Float, nullable=True)


class Database:
    def __init__(self, db_path: str = "data.db"):
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self._create_tables()

    def _create_tables(self):
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def close(self):
        self.engine.dispose()