from abc import ABC, abstractmethod
from typing import List, Optional, Generic, TypeVar
from datetime import date, datetime
from src.domain.models import HeartRateSample, PPISample, ActivitySample, Device, DailySummary

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    def add(self, item: T) -> None:
        pass

    @abstractmethod
    def add_batch(self, items: List[T]) -> None:
        pass

    @abstractmethod
    def get_by_id(self, item_id: int) -> Optional[T]:
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        pass

    @abstractmethod
    def delete(self, item_id: int) -> None:
        pass


class HeartRateRepository(ABC):
    @abstractmethod
    def add(self, sample: HeartRateSample) -> None:
        pass

    @abstractmethod
    def add_batch(self, samples: List[HeartRateSample]) -> None:
        pass

    @abstractmethod
    def get_by_date_range(self, start: datetime, end: datetime, device_id: Optional[str] = None) -> List[HeartRateSample]:
        pass

    @abstractmethod
    def get_latest(self, device_id: Optional[str] = None, limit: int = 1) -> List[HeartRateSample]:
        pass

    @abstractmethod
    def delete_by_date(self, target_date: date, device_id: Optional[str] = None) -> None:
        pass


class PPIRepository(ABC):
    @abstractmethod
    def add(self, sample: PPISample) -> None:
        pass

    @abstractmethod
    def add_batch(self, samples: List[PPISample]) -> None:
        pass

    @abstractmethod
    def get_by_date_range(self, start: datetime, end: datetime, device_id: Optional[str] = None) -> List[PPISample]:
        pass


class ActivityRepository(ABC):
    @abstractmethod
    def add(self, sample: ActivitySample) -> None:
        pass

    @abstractmethod
    def add_batch(self, samples: List[ActivitySample]) -> None:
        pass

    @abstractmethod
    def get_by_date(self, target_date: date) -> List[ActivitySample]:
        pass


class DeviceRepository(ABC):
    @abstractmethod
    def add(self, device: Device) -> None:
        pass

    @abstractmethod
    def get_by_device_id(self, device_id: str) -> Optional[Device]:
        pass

    @abstractmethod
    def get_all(self) -> List[Device]:
        pass