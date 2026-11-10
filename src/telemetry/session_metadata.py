
import json
from datetime import datetime, timezone
from pathlib import Path


def save_session_metadata(
    folder, session_info, participant_info, filename="metadata.json"
):
    """
    Сохраняет информацию о заезде в metadata.json.

    folder — папка конкретной записи.
    session_info — данные Session Packet.
    participant_info — данные Participants Packet.
    """

    # Создаём папку записи, если её ещё нет
    session_folder = Path(folder)
    session_folder.mkdir(parents=True, exist_ok=True)

    # Формируем описание записанной сессии
    metadata = {
        "game": "F1 2025",
        "recorded_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "session": {
            "uid": session_info["session_uid"],
            "track": session_info["track_name"],
            "track_id": session_info["track_id"],
            "session_type": session_info["session_name"],
            "track_length_m": session_info["track_length"],
            "weather_code": session_info["weather"],
            "track_temperature_c": session_info["track_temperature"],
            "air_temperature_c": session_info["air_temperature"],
        },

        "driver": {
            "name": participant_info["driver_name"],
            "team": participant_info["team_name"],
            "team_id": participant_info["team_id"],
            "race_number": participant_info["race_number"],
            "player_index": participant_info["player_index"],
        },
    }

    # Используем индивидуальное имя файла для каждой записи
    file_path = session_folder / filename

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=4
        )

    return file_path
