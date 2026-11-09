
import socket

from PySide6.QtCore import QThread, Signal


class UDPReceiver(QThread):
    # Сигнал отправляет полученный пакет интерфейсу
    packet_received = Signal(bytes)

    # Сигнал сообщает об ошибке приёмника
    error_occurred = Signal(str)

    def __init__(self, port=20777):
        super().__init__()

        # Порт, на который игра отправляет телеметрию
        self.port = port

        # Флаг управления работой потока
        self.running = True

    def run(self):
        """Получает UDP-пакеты в отдельном потоке."""

        udp_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        try:
            # Разрешаем повторное использование адреса
            udp_socket.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )

            # Принимаем пакеты на всех сетевых интерфейсах
            udp_socket.bind(("0.0.0.0", self.port))

            # Проверяем каждые 0.5 секунды,
            # нужно ли остановить поток
            udp_socket.settimeout(0.5)

            while self.running:
                try:
                    data, address = udp_socket.recvfrom(4096)

                    # Передаём пакет в главный поток Qt
                    self.packet_received.emit(data)

                except socket.timeout:
                    continue

        except OSError as error:
            self.error_occurred.emit(str(error))

        finally:
            udp_socket.close()

    def stop(self):
        """Запрашивает остановку приёмника."""
        self.running = False
        self.wait()
