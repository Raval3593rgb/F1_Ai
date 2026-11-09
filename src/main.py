
import sys
import time
from telemetry.packet_parser import (
    parse_car_telemetry,
    parse_car_status,
)
from PySide6.QtCore import QTimer
from telemetry.udp_receiver import UDPReceiver
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QGridLayout,
    QFrame,
)


class F1Assistant(QMainWindow):
    def __init__(self):
        super().__init__()

        # Настройки главного окна приложения
        self.setWindowTitle("F1 AI Assistant")
        self.resize(1200, 750)
        self.setMinimumSize(900, 550)

        # Центральный виджет и горизонтальное расположение элементов
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Боковое меню навигации
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.addItems([
            "Dashboard",
            "Live Telemetry",
            "Lap Analysis",
            "AI Assistant",
            "Settings",
        ])

        # Контейнер для переключения страниц
        self.pages = QStackedWidget()

        for page_name in [
            "Dashboard",
            "Live Telemetry",
            "Lap Analysis",
            "AI Assistant",
            "Settings",
        ]:
            self.pages.addWidget(self.create_page(page_name))

        # Сигнал смены выбранного пункта меню
        self.sidebar.currentRowChanged.connect(
            self.pages.setCurrentIndex
        )

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.pages)

        # Устанавливаем тёмную тему
        self.apply_theme()

        # Показываем Dashboard при запуске
        self.sidebar.setCurrentRow(0)

        # Время получения последнего UDP-пакета
        self.last_packet_time = None

        # Создаём UDP-приёмник
        self.udp_receiver = UDPReceiver(port=20777)

        # Подключаем сигналы приёмника
        self.udp_receiver.packet_received.connect(
            self.on_packet_received
        )

        self.udp_receiver.error_occurred.connect(
            self.on_udp_error
        )

        # Запускаем отдельный поток
        self.udp_receiver.start()

        # Проверяем состояние соединения каждые 500 мс
        self.connection_timer = QTimer(self)
        self.connection_timer.timeout.connect(
            self.check_connection
        )
        self.connection_timer.start(500)



    def create_telemetry_card(self, title, value, unit):
        """Создаёт карточку с показателем телеметрии."""

        # Внешний контейнер карточки
        card = QFrame()
        card.setObjectName("telemetryCard")
        card.setMinimumHeight(150)

        # Вертикальное расположение элементов
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Название показателя
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")

        # Значение и единица измерения
        value_label = QLabel(f"{value} {unit}".strip())
        value_label.setObjectName("cardValue")
        # Сохраняем ссылку на QLabel, чтобы менять значение
        card.value_label = value_label

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()

        return card


    
    def create_connection_status(self):
        """Создаёт индикатор UDP-соединения."""

        # Текстовый индикатор подключения
        self.connection_label = QLabel("● UDP DISCONNECTED")
        self.connection_label.setObjectName("connectionStatus")

        return self.connection_label



    def create_page(self, page_name):
        """Создаёт страницу приложения."""

        page = QWidget()
        layout = QVBoxLayout(page)

        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(25)

        # Заголовок страницы
        title = QLabel(page_name)
        title.setObjectName("pageTitle")

        layout.addWidget(title)

        if page_name == "Dashboard":
            

            # Показываем состояние UDP-подключения
            connection_status = self.create_connection_status()
            layout.addWidget(connection_status)

            # Сетка для карточек телеметрии
            grid = QGridLayout()
            grid.setSpacing(20)

            
            # Сохраняем карточки как атрибуты класса
            self.speed_card = self.create_telemetry_card(
                "SPEED", "0", "km/h"
            )

            self.rpm_card = self.create_telemetry_card(
                "ENGINE RPM", "0", "RPM"
            )

            self.gear_card = self.create_telemetry_card(
                "GEAR", "N", ""
            )

            self.fuel_card = self.create_telemetry_card(
                "FUEL", "--", "kg"
            )

            # Размещаем карточки в сетке
            grid.addWidget(self.speed_card, 0, 0)
            grid.addWidget(self.rpm_card, 0, 1)
            grid.addWidget(self.gear_card, 1, 0)
            grid.addWidget(self.fuel_card, 1, 1)


            layout.addLayout(grid)

        layout.addStretch()

        return page

    
    
    
   
    def on_packet_received(self, data):
        """Обрабатывает телеметрию и состояние машины."""

        # Запоминаем время последнего UDP-пакета
        self.last_packet_time = time.monotonic()

        # Пакет Car Telemetry: скорость, RPM, передача
        telemetry = parse_car_telemetry(data)

        if telemetry is not None:
            self.speed_card.value_label.setText(
                f"{telemetry['speed']} km/h"
            )

            self.rpm_card.value_label.setText(
                f"{telemetry['rpm']} RPM"
            )

            self.gear_card.value_label.setText(
                telemetry["gear"]
            )

        # Пакет Car Status: количество топлива
        status = parse_car_status(data)

        if status is not None:
            self.fuel_card.value_label.setText(
                f"{status['fuel']:.1f} kg"
            )



    def check_connection(self):
        """Проверяет, поступали ли пакеты недавно."""

        connected = (
            self.last_packet_time is not None
            and time.monotonic() - self.last_packet_time < 2
        )

        if connected:
            self.connection_label.setText("● UDP CONNECTED")
            self.connection_label.setStyleSheet(
                "color: #22C55E;"
            )
        else:
            self.connection_label.setText("● UDP DISCONNECTED")
            self.connection_label.setStyleSheet(
                "color: #EF4444;"
            )

    def on_udp_error(self, error):
        """Выводит ошибки UDP-приёмника."""
        print(f"UDP error: {error}")

    def closeEvent(self, event):
        """Останавливает UDP-поток при закрытии окна."""
        self.connection_timer.stop()
        self.udp_receiver.stop()
        event.accept()



    def apply_theme(self):
        """Применяет базовые стили ко всему приложению."""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #101218;
                color: #F1F3F5;
                font-family: "Segoe UI";
            }

            QListWidget {
                background-color: #181C25;
                border: none;
                padding: 15px 8px;
                font-size: 15px;
                outline: none;
            }

            QListWidget::item {
                padding: 15px;
                margin-bottom: 5px;
                border-radius: 8px;
            }

            QListWidget::item:hover {
                background-color: #292F3D;
            }

            QListWidget::item:selected {
                background-color: #C62828;
                color: white;
            }

            QLabel#pageTitle {
                font-size: 32px;
                font-weight: bold;
            }


            QFrame#telemetryCard {
            background-color: #1C2230;
            border: 1px solid #303849;
            border-radius: 12px;
            }

            QLabel#cardTitle {
            color: #98A2B3;
            font-size: 14px;
            font-weight: bold;
            }

            QLabel#cardValue {
                color: #FFFFFF;
                font-size: 38px;
                font-weight: bold;
            }

            QLabel#pageTitle {
                font-size: 28px;
                font-weight: bold;
            }

            QFrame#telemetryCard {
                background-color: transparent;
                border: none;
            }


            QLabel#connectionStatus {
                color: #EF4444;
                background-color: transparent;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 0;
            }
        """)


if __name__ == "__main__":
    # QApplication управляет жизненным циклом GUI
    app = QApplication(sys.argv)

    window = F1Assistant()
    window.show()

    # Запускаем цикл обработки событий приложения
    sys.exit(app.exec())
