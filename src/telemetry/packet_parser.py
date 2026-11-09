
import struct


def parse_car_telemetry(data):
    """Расшифровывает телеметрию машины игрока F1 2025."""

    # Проверяем размер пакета и формат F1 2025
    if len(data) != 1352:
        return None

    packet_format = struct.unpack_from("<H", data, 0)[0]

    if packet_format != 2025:
        return None

    # Тип UDP-пакета находится в байте 6
    packet_id = data[6]

    # Нам нужен только Car Telemetry (ID = 6)
    if packet_id != 6:
        return None

    # Индекс машины игрока находится в байте 27
    player_index = data[27]

    if player_index >= 22:
        return None

    # Заголовок занимает 29 байт
    # Данные каждой машины занимают 60 байт
    offset = 29 + player_index * 60

    # Расшифровываем скорость, передачу и обороты
    speed = struct.unpack_from("<H", data, offset)[0]
    gear = struct.unpack_from("<b", data, offset + 15)[0]
    rpm = struct.unpack_from("<H", data, offset + 16)[0]

    # Преобразуем передачу в понятный вид
    if gear == 0:
        gear_display = "N"
    elif gear == -1:
        gear_display = "R"
    else:
        gear_display = str(gear)

    return {
        "speed": speed,
        "gear": gear_display,
        "rpm": rpm,
    }



def parse_car_status(data):
    """Получает количество топлива машины игрока."""

    # Проверяем размер пакета Car Status
    if len(data) != 1239:
        return None

    # Проверяем формат телеметрии F1 2025
    packet_format = struct.unpack_from("<H", data, 0)[0]

    if packet_format != 2025:
        return None

    # Car Status имеет ID = 7
    if data[6] != 7:
        return None

    # Определяем машину игрока
    player_index = data[27]

    if player_index >= 22:
        return None

    # Заголовок 29 байт, каждая машина — 55 байт
    offset = 29 + player_index * 55

    # Первые 5 байт — параметры автомобиля
    # Затем идёт float с количеством топлива в кг
    fuel = struct.unpack_from("<f", data, offset + 5)[0]

    return {
        "fuel": fuel
    }
