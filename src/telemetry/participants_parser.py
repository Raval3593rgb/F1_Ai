
import struct


# Команды F1 2025
TEAM_NAMES = {
    0: "Mercedes",
    1: "Ferrari",
    2: "Red Bull Racing",
    3: "Williams",
    4: "Aston Martin",
    5: "Alpine",
    6: "Racing Bulls",
    7: "Haas",
    8: "McLaren",
    9: "Sauber",
    41: "F1 Generic",
    104: "Custom Team",
    129: "Konnersport",
    154: "APXGP 2025",
}


def parse_participants(data):
    """Извлекает сведения о машине игрока из F1 2025."""

    # Проверяем формат и идентификатор пакета
    if len(data) != 1284:
        return None

    packet_format = struct.unpack_from("<H", data, 0)[0]
    packet_id = data[6]

    if packet_format != 2025 or packet_id != 4:
        return None

    # Индекс управляемой игроком машины
    player_index = data[27]

    # Количество участников
    num_active_cars = data[29]

    if player_index >= num_active_cars or player_index >= 22:
        return None

    # Каждый участник занимает 57 байт
    participant_size = 57
    offset = 30 + player_index * participant_size

    ai_controlled = data[offset]
    driver_id = data[offset + 1]
    team_id = data[offset + 3]
    race_number = data[offset + 5]

    # Имя участника — строка UTF-8
    name_bytes = data[offset + 7:offset + 39]
    driver_name = (
        name_bytes.split(b"\x00", 1)[0]
        .decode("utf-8", errors="replace")
    )

    return {
        "session_uid": struct.unpack_from("<Q", data, 7)[0],
        "player_index": player_index,
        "driver_id": driver_id,
        "driver_name": driver_name,
        "team_id": team_id,
        "team_name": TEAM_NAMES.get(
            team_id, f"Unknown Team ({team_id})"
        ),
        "race_number": race_number,
        "ai_controlled": bool(ai_controlled),
    }
