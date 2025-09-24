from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AppConfig:
    data_directory: Path = Path("loop_data")
    database_path: str = "data.db"
    max_heart_rate: int = 190
    user_weight_kg: float = 70.0

    refresh_interval_seconds: int = 5

    # TUI configuration
    show_grid: bool = True
    show_legend: bool = True
    theme: str = "dark"

    def __post_init__(self):
        if not self.data_directory.exists():
            raise ValueError(f"Data directory {self.data_directory} does not exist")


config = AppConfig()