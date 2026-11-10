
import sys
import csv
import time
from datetime import datetime
from pathlib import Path


class DataLogger:
    """Сохраняет телеметрию F1 2025 в CSV-файл."""

    def __init__(self):
        # Определяем корневую папку проекта
        if getattr(sys, "frozen", False):
            self.project_dir = Path(sys.executable).resolve().parent
        else:
            self.project_dir = Path(__file__).resolve().parents[2]

        # Создаём папку для сохранения заездов
        self.data_dir = self.project_dir / "data" / "sessions"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Состояние записи
        self.recording = False

        self.file = None
        self.writer = None
        self.start_time = None
        self.current_filepath = None

        # Последние полученные данные
        self.last_fuel = None
        self.last_lap_info = None

    def start(self):
        """Начинает новую запись телеметрии."""

        if self.recording:
            return

        # Генерируем уникальное имя CSV по дате и времени
        filename = datetime.now().strftime(
            "session_%Y%m%d_%H%M%S_%f.csv"
        )

        filepath = self.data_dir / filename

        # Запоминаем путь к файлу для metadata.json
        self.current_filepath = filepath

        # Сбрасываем данные предыдущего круга и топлива
        self.last_lap_info = None
        self.last_fuel = None

        # Открываем новый CSV-файл
        self.file = open(
            filepath,
            "w",
            newline="",
            encoding="utf-8"
        )

        self.writer = csv.writer(self.file)

        # Заголовки CSV
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
            "lap_number",
            "sector",
            "lap_distance_m",
            "lap_time_s",
            "lap_valid",
        ])

        # Время начала записи
        self.start_time = time.monotonic()
        self.recording = True

        print(f"Recording started: {filepath}")

    def update_fuel(self, fuel):
        """Сохраняет последнее полученное значение топлива."""

        self.last_fuel = fuel

    def update_lap(self, lap_info):
        """Обновляет информацию о текущем круге."""

        # Сохраняем копию данных из Lap Data Packet
        self.last_lap_info = dict(lap_info)

    def log(self, telemetry):
        """Записывает одну строку телеметрии в CSV."""

        if not self.recording:
            return

        # Время с начала записи
        elapsed = time.monotonic() - self.start_time

        # Температуры шин
        surface = telemetry["tyres_surface"]
        inner = telemetry["tyres_inner"]

        # Получаем последние данные о круге
        lap = self.last_lap_info

        # Если информация о круге ещё не поступила,
        # соответствующие значения останутся пустыми
        lap_number = lap["current_lap"] if lap else ""
        sector = lap["sector"] if lap else ""
        lap_distance = lap["lap_distance"] if lap else ""
        lap_time = lap["current_lap_time"] if lap else ""
        lap_valid = not lap["lap_invalid"] if lap else ""

        # Записываем все 18 значений в одну строку
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
            lap_number,
            sector,
            round(lap_distance, 2) if lap else "",
            round(lap_time, 3) if lap else "",
            lap_valid,
        ])

    def stop(self):
        """Останавливает запись и закрывает CSV-файл."""

        if not self.recording:
            return None

        self.recording = False

        # Сбрасываем буфер и закрываем файл
        self.file.flush()
        self.file.close()

        self.file = None
        self.writer = None

        print("Recording stopped.")

        # Возвращаем путь для сохранения metadata.json
        return self.current_filepath
