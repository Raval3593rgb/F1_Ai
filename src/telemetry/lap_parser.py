
import struct


def parse_lap_data(data):
    """
    Получает информацию о текущем круге игрока
    из UDP-пакета Lap Data (ID 2) F1 2025.
    """

    # Проверяем размер пакета
    if len(data) != 1285:
        return None

    # Проверяем формат F1 2025 и тип пакета
    packet_format = struct.unpack_from("<H", data, 0)[0]
    packet_id = data[6]

    if packet_format != 2025 or packet_id != 2:
        return None

    # Уникальный идентификатор сессии
    session_uid = struct.unpack_from("<Q", data, 7)[0]

    # Индекс автомобиля, которым управляет игрок
    player_index = data[27]

    if player_index >= 22:
        return None

    # Заголовок 29 байт + данные предыдущих машин
    offset = 29 + player_index * 57

    # Время текущего и предыдущего круга
    last_lap_ms = struct.unpack_from(
        "<I", data, offset
    )[0]

    current_lap_ms = struct.unpack_from(
        "<I", data, offset + 4
    )[0]

    # Пройденная дистанция внутри текущего круга
    lap_distance = struct.unpack_from(
        "<f", data, offset + 20
    )[0]

    # Общая дистанция за сессию
    total_distance = struct.unpack_from(
        "<f", data, offset + 24
    )[0]

   
    # Номер текущего круга
    current_lap = data[offset + 33]

    # Номер сектора, полученный из игры: 0, 1 или 2
    sector = data[offset + 36]

    # Преобразуем номера секторов:
    # 0 -> сектор 1
    # 1 -> сектор 2
    # 2 -> сектор 3
    sector_number = sector + 1 if sector in (0, 1, 2) else None

    # Проверяем действительность круга
    lap_invalid = bool(data[offset + 37])


    return {
        "session_uid": session_uid,
        "player_index": player_index,
        "current_lap": current_lap,
        "sector": sector_number,
        "lap_distance": lap_distance,
        "total_distance": total_distance,
        "current_lap_time": current_lap_ms / 1000,
        "last_lap_time": last_lap_ms / 1000,
        "lap_invalid": lap_invalid,
    }
