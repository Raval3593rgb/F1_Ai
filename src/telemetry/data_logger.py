
import csv
import time
from datetime import datetime
from pathlib import Path


class DataLogger:
    """Сохраняет телеметрию F1 2025 в CSV-файл."""

    def __init__(self):
        # Корневая папка проекта
        self.project_dir = Path(__file__).resolve().parents[2]

        # Папка для записанных заездов
        self.data_dir = self.project_dir / "data" / "sessions"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Состояние записи
        self.recording = False

        self.file = None
        self.writer = None
        self.start_time = None

        # Последние полученные значения топлива
        self.last_fuel = None

    def start(self):
        """Начинает новую запись телеметрии."""

        if self.recording:
            return

        # Уникальное имя файла по дате и времени
        filename = datetime.now().strftime(
            "session_%Y%m%d_%H%M%S_%f.csv"
        )

        filepath = self.data_dir / filename

        # Открываем CSV-файл
        self.file = open(
            filepath,
            "w",
            newline="",
            encoding="utf-8"
        )

        # Создаём CSV-писатель
        self.writer = csv.writer(self.file)

        # Заголовки столбцов
        self.writer.writerow([
            "time_s",
            "speed_kmh",
            "rpm",
            "gear",
            "fuel_kg",
            "tyre_fl_surface",
            "tyre_fr_surface",
            "tyre_rl_surface",
            "tyre_rr_surface",
            "tyre_fl_inner",
            "tyre_fr_inner",
            "tyre_rl_inner",
            "tyre_rr_inner",
        ])

        self.start_time = time.monotonic()
        self.recording = True

        print(f"Recording started: {filepath}")

    def update_fuel(self, fuel):
        """Запоминает последнее значение топлива."""
        self.last_fuel = fuel

    def log(self, telemetry):
        """Записывает одну строку телеметрии."""

        if not self.recording:
            return

        elapsed = time.monotonic() - self.start_time

        surface = telemetry["tyres_surface"]
        inner = telemetry["tyres_inner"]

        self.writer.writerow([
            round(elapsed, 3),
            telemetry["speed"],
            telemetry["rpm"],
            telemetry["gear"],
            self.last_fuel if self.last_fuel is not None else "",
            surface["FL"],
            surface["FR"],
            surface["RL"],
            surface["RR"],
            inner["FL"],
            inner["FR"],
            inner["RL"],
            inner["RR"],
        ])

    def stop(self):
        """Завершает запись и закрывает CSV-файл."""

        if not self.recording:
            return

        self.recording = False

        self.file.close()
        self.file = None
        self.writer = None

        print("Recording stopped.")
