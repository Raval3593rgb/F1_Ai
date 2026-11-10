
import struct


def parse_session(data):
    """Извлекает основные сведения о сессии F1 2025."""

    # Проверяем длину Session Packet для формата 2025.
    if len(data) != 753:
        return None

    # Первые два байта — год формата телеметрии.
    packet_format = struct.unpack_from("<H", data, 0)[0]

    # Байt 6 — идентификатор типа UDP-пакета.
    packet_id = data[6]

    if packet_format != 2025 or packet_id != 1:
        return None

    # Уникальный идентификатор игровой сессии.
    session_uid = struct.unpack_from("<Q", data, 7)[0]

    # Информация Session Packet начинается с байта 29.
    weather = data[29]
    track_temperature = struct.unpack_from("<b", data, 30)[0]
    air_temperature = struct.unpack_from("<b", data, 31)[0]
    total_laps = data[32]
    track_length = struct.unpack_from("<H", data, 33)[0]
    session_type = data[35]
    track_id = struct.unpack_from("<b", data, 36)[0]

    return {
        "session_uid": session_uid,
        "track_id": track_id,
        "session_type": session_type,
        "weather": weather,
        "track_temperature": track_temperature,
        "air_temperature": air_temperature,
        "total_laps": total_laps,
        "track_length": track_length,
        "track_name": TRACK_NAMES.get(track_id, f"Unknown ({track_id})"),
        "session_name": SESSION_TYPES.get(session_type, f"Unknown ({session_type})"),

    }



# Названия трасс по идентификаторам F1 2025
TRACK_NAMES = {
    0: "Melbourne",
    2: "Shanghai",
    3: "Bahrain",
    4: "Catalunya",
    5: "Monaco",
    6: "Montreal",
    7: "Silverstone",
    9: "Hungaroring",
    10: "Spa-Francorchamps",
    11: "Monza",
    12: "Singapore",
    13: "Suzuka",
    14: "Abu Dhabi",
    15: "Austin",
    16: "Interlagos",
    17: "Spielberg",
    19: "Mexico City",
    20: "Baku",
    26: "Zandvoort",
    27: "Imola",
    29: "Jeddah",
    30: "Miami",
    31: "Las Vegas",
    32: "Lusail",
    39: "Silverstone Reverse",
    40: "Austria Reverse",
    41: "Zandvoort Reverse",
}

# Типы игровых сессий
SESSION_TYPES = {
    0: "Unknown",
    1: "Practice 1",
    2: "Practice 2",
    3: "Practice 3",
    4: "Short Practice",
    5: "Qualifying 1",
    6: "Qualifying 2",
    7: "Qualifying 3",
    8: "Short Qualifying",
    9: "One-Shot Qualifying",
    10: "Sprint Shootout 1",
    11: "Sprint Shootout 2",
    12: "Sprint Shootout 3",
    13: "Short Sprint Shootout",
    14: "One-Shot Sprint Shootout",
    15: "Race",
    16: "Race 2",
    17: "Race 3",
    18: "Time Trial",
}
