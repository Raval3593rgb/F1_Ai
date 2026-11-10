
import csv


def split_laps(csv_path, track_length=None):
    """
    Разделяет записанную телеметрию на отдельные
    круги или попытки по сбросу дистанции.

    csv_path — путь к CSV-файлу.
    track_length — длина трассы в метрах.
    """

    # Загружаем записанную телеметрию
    with open(csv_path, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    if not rows:
        return []

    laps = []
    current_lap = []

    # Собственный идентификатор круга внутри записи
    lap_id = 1

    previous_distance = None

    for row in rows:

        # Данные дистанции могут отсутствовать
        try:
            distance = float(row["lap_distance_m"])
        except (ValueError, TypeError, KeyError):
            distance = None

        if previous_distance is not None and distance is not None:

            # Обнаруживаем резкий сброс дистанции
            distance_reset = (
                previous_distance - distance > 1000
            )

            # Если знаем длину трассы, дополнительно
            # проверяем близость к старт-финишу
            near_finish = (
                track_length is None
                or previous_distance >= track_length - 150
            )

            if distance_reset and near_finish:

                # Завершаем предыдущий сегмент
                if current_lap:
                    laps.append({
                        "lap_id": lap_id,
                        "rows": current_lap,
                    })

                lap_id += 1
                current_lap = []

        # Добавляем измерение в текущий круг
        current_lap.append(row)

        if distance is not None:
            previous_distance = distance

    # Сохраняем последний сегмент
    if current_lap:
        laps.append({
            "lap_id": lap_id,
            "rows": current_lap,
        })

    return laps
