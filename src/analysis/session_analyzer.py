
import csv
import json
import math

from pathlib import Path
from statistics import mean

from analysis.lap_splitter import split_laps


class SessionAnalyzer:
    """Анализирует полную сессию и отдельные круги F1."""

    TYRES = ("fl", "fr", "rl", "rr")

    def __init__(self, filepath):
        self.filepath = Path(filepath)

        # Все измерения загруженной сессии
        self.data = []

        # Отдельные круги и попытки
        self.laps = []

        # None означает анализ всей сессии
        self.selected_lap_id = None

        # Метаданные записанного заезда
        self.metadata = {}
        self.track_length = None

    @staticmethod
    def read_number(row, key):
        """Безопасно преобразует значение CSV в число."""

        try:
            value = float(row[key])

            if math.isfinite(value):
                return value

        except (ValueError, KeyError, TypeError):
            pass

        return math.nan

    def load_metadata(self):
        """Загружает JSON с описанием трассы и пилота."""

        metadata_path = self.filepath.with_suffix(
            ".metadata.json"
        )

        self.metadata = {}
        self.track_length = None

        if not metadata_path.exists():
            return

        with metadata_path.open(
            "r", encoding="utf-8"
        ) as file:
            self.metadata = json.load(file)

        length = self.metadata.get(
            "session", {}
        ).get("track_length_m")

        if isinstance(length, (int, float)) and length > 0:
            self.track_length = length

    def parse_sample(self, row):
        """Преобразует строку CSV в измерение."""

        time_s = self.read_number(row, "time_s")
        speed = self.read_number(row, "speed_kmh")
        rpm = self.read_number(row, "rpm")

        if not all(
            math.isfinite(value)
            for value in (time_s, speed, rpm)
        ):
            return None

        sample = {
            "time": time_s,
            "speed": speed,
            "rpm": rpm,
            "fuel": self.read_number(row, "fuel_kg"),

            # Дополнительные поля Data Logger 2.0
            "lap_number": self.read_number(
                row, "lap_number"
            ),
            "sector": self.read_number(
                row, "sector"
            ),
            "lap_distance": self.read_number(
                row, "lap_distance_m"
            ),
            "lap_time": self.read_number(
                row, "lap_time_s"
            ),
            "lap_valid": row.get("lap_valid", ""),
        }

        # Температуры всех четырёх шин
        for tyre in self.TYRES:

            sample[f"tyre_{tyre}"] = self.read_number(
                row, f"tyre_{tyre}_surface"
            )

            sample[f"inner_{tyre}"] = self.read_number(
                row, f"tyre_{tyre}_inner"
            )

        return sample

    def load(self):
        """Загружает CSV и разделяет его на круги."""

        self.data.clear()
        self.laps.clear()
        self.selected_lap_id = None

        self.load_metadata()

        # Проверяем, содержит ли CSV данные о кругах
        with self.filepath.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames or []

        has_lap_data = "lap_distance_m" in fieldnames

        # Используем наш существующий алгоритм
        segments = split_laps(
            self.filepath,
            track_length=self.track_length
        )

        for segment in segments:

            samples = []

            for row in segment["rows"]:
                sample = self.parse_sample(row)

                if sample is not None:
                    samples.append(sample)

            if not samples:
                continue

            samples.sort(
                key=lambda item: item["time"]
            )

            self.data.extend(samples)

            # Старые CSV показываем только как Full Session
            if not has_lap_data:
                continue

            first_distance = samples[0]["lap_distance"]
            last_distance = samples[-1]["lap_distance"]

            self.laps.append({
                "lap_id": segment["lap_id"],
                "samples": samples,
                "first_distance": first_distance,
                "last_distance": last_distance,
                "game_lap": samples[0]["lap_number"],
            })

        # Сохраняем хронологический порядок
        self.data.sort(key=lambda item: item["time"])

        return len(self.data)

    def select_lap(self, lap_id=None):
        """
        Выбирает круг для анализа.
        None — вся сессия.
        """

        if lap_id is None:
            self.selected_lap_id = None
            return

        if any(
            lap["lap_id"] == lap_id
            for lap in self.laps
        ):
            self.selected_lap_id = lap_id

    def get_active_data(self):
        """Возвращает измерения выбранного круга."""

        if self.selected_lap_id is None:
            return self.data

        for lap in self.laps:
            if lap["lap_id"] == self.selected_lap_id:
                return lap["samples"]

        return []

    def get_selected_lap(self):
        """Возвращает информацию о выбранном круге."""

        for lap in self.laps:
            if lap["lap_id"] == self.selected_lap_id:
                return lap

        return None

    def get_statistics(self):
        """Вычисляет статистику выбранного набора данных."""

        data = self.get_active_data()

        if not data:
            return None

        speeds = [row["speed"] for row in data]
        rpms = [row["rpm"] for row in data]

        valid_fuel = [
            row["fuel"]
            for row in data
            if math.isfinite(row["fuel"])
        ]

        return {
            "max_speed": max(speeds),
            "avg_speed": mean(speeds),
            "max_rpm": max(rpms),
            "duration": max(
                0,
                data[-1]["time"] - data[0]["time"]
            ),
            "samples": len(data),
            "fuel_start": (
                valid_fuel[0] if valid_fuel else None
            ),
            "fuel_end": (
                valid_fuel[-1] if valid_fuel else None
            ),
        }

    def get_series(self, key):
        """Возвращает данные для построения графика."""

        data = self.get_active_data()

        if not data:
            return [], []

        # При выборе отдельного круга
        # начинаем ось времени с нуля
        start_time = (
            data[0]["time"]
            if self.selected_lap_id is not None
            else 0
        )

        times = [
            row["time"] - start_time
            for row in data
        ]

        values = [
            row.get(key, math.nan)
            for row in data
        ]

        return times, values
