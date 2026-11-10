
import csv
import math
from pathlib import Path
from statistics import mean


class SessionAnalyzer:
    """Загружает и анализирует телеметрию F1 из CSV."""

    # Обозначения четырёх колёс
    TYRES = ("fl", "fr", "rl", "rr")

    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.data = []

    @staticmethod
    def read_number(row, key):
        """Безопасно преобразует значение CSV в число."""

        try:
            value = float(row[key])

            # Исключаем бесконечные значения и NaN
            if math.isfinite(value):
                return value

        except (ValueError, KeyError, TypeError):
            pass

        # Если данных нет, возвращаем NaN
        return math.nan

    def load(self):
        """Загружает записанную телеметрию."""

        self.data.clear()

        with self.filepath.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                try:
                    # Основные показатели
                    time_s = float(row["time_s"])
                    speed = float(row["speed_kmh"])
                    rpm = float(row["rpm"])

                    # Пропускаем некорректные измерения
                    if not all(
                        math.isfinite(v)
                        for v in (time_s, speed, rpm)
                    ):
                        continue

                    sample = {
                        "time": time_s,
                        "speed": speed,
                        "rpm": rpm,

                        # Количество топлива
                        "fuel": self.read_number(
                            row, "fuel_kg"
                        ),
                    }

                    # Температуры четырёх шин
                    for tyre in self.TYRES:

                        # Температура поверхности
                        sample[f"tyre_{tyre}"] = (
                            self.read_number(
                                row,
                                f"tyre_{tyre}_surface"
                            )
                        )

                        # Внутренняя температура
                        sample[f"inner_{tyre}"] = (
                            self.read_number(
                                row,
                                f"tyre_{tyre}_inner"
                            )
                        )

                    self.data.append(sample)

                except (ValueError, KeyError, TypeError):
                    continue

        # Сортируем измерения по времени
        self.data.sort(
            key=lambda sample: sample["time"]
        )

        return len(self.data)

    def get_statistics(self):
        """Вычисляет статистику записанной сессии."""

        if not self.data:
            return None

        speeds = [
            sample["speed"]
            for sample in self.data
        ]

        rpms = [
            sample["rpm"]
            for sample in self.data
        ]

        # Убираем пропущенные значения топлива
        valid_fuel = [
            sample["fuel"]
            for sample in self.data
            if math.isfinite(sample["fuel"])
        ]

        return {
            "max_speed": max(speeds),
            "avg_speed": mean(speeds),
            "max_rpm": max(rpms),

            "duration": max(
                0,
                self.data[-1]["time"]
                - self.data[0]["time"]
            ),

            "samples": len(self.data),

            "fuel_start": (
                valid_fuel[0]
                if valid_fuel else None
            ),

            "fuel_end": (
                valid_fuel[-1]
                if valid_fuel else None
            ),
        }

    def get_series(self, key):
        """Возвращает временные метки и значения параметра."""

        if not self.data:
            return [], []

        times = [
            sample["time"]
            for sample in self.data
        ]

        values = [
            sample.get(key, math.nan)
            for sample in self.data
        ]

        return times, values
