import sys
import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from telemetry.packet_parser import parse_car_status, parse_car_telemetry
from telemetry.udp_receiver import UDPReceiver
from widgets.telemetry_graph import TelemetryGraph
from PySide6.QtWidgets import QPushButton
from telemetry.data_logger import DataLogger
from widgets.lap_analysis_page import LapAnalysisPage


class F1Assistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data_logger = DataLogger()
        self.setWindowTitle("F1 AI Assistant")
        self.resize(1250, 800)
        self.setMinimumSize(900, 550)

        self.last_packet_time = None
        self.last_telemetry_time = 0.0
        self.last_fuel_time = 0.0
        self.last_graph_sample_time = 0.0

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.addItems([
            "Dashboard", "Live Telemetry", "Lap Analysis", "AI Assistant", "Settings"
        ])
        self.pages = QStackedWidget()
        for name in [
            "Dashboard", "Live Telemetry", "Lap Analysis", "AI Assistant", "Settings"
        ]:
            if name == "Live Telemetry":
                # Страница графиков реального времени
                page = self.create_live_page()

            elif name == "Lap Analysis":
                # Страница анализа сохранённых CSV
                page = LapAnalysisPage()

            else:
                # Остальные страницы приложения
                page = self.create_page(name)

            self.pages.addWidget(page)

        self.sidebar.currentRowChanged.connect(self.pages.setCurrentIndex)
        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.pages)
        self.apply_theme()
        self.sidebar.setCurrentRow(0)

        # Приёмник UDP работает в отдельном потоке.
        self.udp_receiver = UDPReceiver(port=20777)
        self.udp_receiver.packet_received.connect(self.on_packet_received)
        self.udp_receiver.error_occurred.connect(self.on_udp_error)
        self.udp_receiver.start()

        self.connection_timer = QTimer(self)
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(500)

        self.graph_timer = QTimer(self)
        self.graph_timer.timeout.connect(self.update_graphs)
        self.graph_timer.start(50)  # максимум 20 перерисовок/с

    def create_telemetry_card(self, name, initial_value):
        card = QFrame()
        card.setObjectName("telemetryCard")
        card.setMinimumHeight(135)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)

        title = QLabel(name)
        title.setObjectName("cardTitle")
        value = QLabel(initial_value)
        value.setObjectName("cardValue")
        layout.addWidget(title)
        layout.addWidget(value)
        layout.addStretch()
        card.value_label = value
        return card

    def create_tyre_panel(self):
        panel = QFrame()
        panel.setObjectName("tyrePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        title = QLabel("TYRE TEMPERATURES")
        title.setObjectName("cardTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)
        self.tyre_labels = {}
        for index, (key, name) in enumerate([
            ("FL", "FRONT LEFT"), ("FR", "FRONT RIGHT"),
            ("RL", "REAR LEFT"), ("RR", "REAR RIGHT"),
        ]):
            card = QFrame()
            card.setObjectName("tyreCard")
            column = QVBoxLayout(card)
            column.setContentsMargins(15, 15, 15, 15)
            name_label = QLabel(name)
            name_label.setObjectName("tyreName")
            surface_label = QLabel("Surface: --°C")
            surface_label.setObjectName("tyreSurface")
            inner_label = QLabel("Inner: --°C")
            inner_label.setObjectName("tyreInner")
            for widget in (name_label, surface_label, inner_label):
                column.addWidget(widget)
            self.tyre_labels[key] = {"surface": surface_label, "inner": inner_label}
            grid.addWidget(card, index // 2, index % 2)

        layout.addLayout(grid)
        return panel


    def create_recording_controls(self):
        """Создаёт кнопки управления записью телеметрии."""

        panel = QWidget()
        layout = QHBoxLayout(panel)

        # Кнопка начала записи
        self.start_button = QPushButton("● Start Recording")
        self.start_button.clicked.connect(self.start_recording)

        # Кнопка остановки записи
        self.stop_button = QPushButton("■ Stop Recording")
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)

        # Индикатор состояния записи
        self.recording_label = QLabel("NOT RECORDING")

        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.recording_label)
        layout.addStretch()

        return panel


    def create_page(self, name):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(20)
        title = QLabel(name)
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        if name == "Dashboard":
            self.connection_label = QLabel("● UDP DISCONNECTED")
            self.connection_label.setObjectName("connectionStatus")
            layout.addWidget(self.connection_label)
            recording_controls = self.create_recording_controls()
            layout.addWidget(recording_controls)

            grid = QGridLayout()
            grid.setSpacing(16)
            self.speed_card = self.create_telemetry_card("SPEED", "0 km/h")
            self.rpm_card = self.create_telemetry_card("ENGINE RPM", "0 RPM")
            self.gear_card = self.create_telemetry_card("GEAR", "N")
            self.fuel_card = self.create_telemetry_card("FUEL", "-- kg")
            for card, row, col in (
                (self.speed_card, 0, 0), (self.rpm_card, 0, 1),
                (self.gear_card, 1, 0), (self.fuel_card, 1, 1),
            ):
                grid.addWidget(card, row, col)
            layout.addLayout(grid)
            layout.addWidget(self.create_tyre_panel())
            layout.addStretch()

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setWidget(page)
            return scroll

        layout.addStretch()
        return page

    def create_live_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(20)
        title = QLabel("Live Telemetry")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.speed_graph = TelemetryGraph("SPEED (km/h)", {"Speed": "#EF4444"})
        self.rpm_graph = TelemetryGraph("ENGINE RPM", {"RPM": "#3B82F6"})
        self.fuel_graph = TelemetryGraph("FUEL (kg)", {"Fuel": "#F59E0B"})
        self.tyre_graph = TelemetryGraph(
            "TYRE SURFACE TEMPERATURE (°C)",
            {"FL": "#22C55E", "FR": "#F97316", "RL": "#38BDF8", "RR": "#A78BFA"},
        )
        for graph in (self.speed_graph, self.rpm_graph, self.fuel_graph, self.tyre_graph):
            layout.addWidget(graph)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(page)
        return scroll

    @staticmethod
    def get_tyre_color(temperature):
        # Условные визуальные диапазоны; не являются советом по оптимальному нагреву.
        if temperature < 85:
            return "#60A5FA"
        if temperature <= 105:
            return "#4ADE80"
        return "#FB923C"

    
    def start_recording(self):
        """Начинает запись телеметрии."""

        self.data_logger.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.recording_label.setText("● RECORDING")
        self.recording_label.setStyleSheet(
            "color: #EF4444; font-weight: bold;"
        )

    def stop_recording(self):
        """Завершает запись телеметрии."""

        self.data_logger.stop()

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.recording_label.setText("NOT RECORDING")
        self.recording_label.setStyleSheet(
            "color: #98A2B3;"
        )


    def on_packet_received(self, data):
        
        now = time.monotonic()
        
        self.last_packet_time = now
        
        telemetry = parse_car_telemetry(data)

        if telemetry is not None:
         
            # GUI обновляем до 20 раз/с, даже если пакеты приходят чаще.
            if self.data_logger.recording:
                self.data_logger.log(telemetry)
            
            if now - self.last_telemetry_time >= 0.05:
                self.last_telemetry_time = now
                self.speed_card.value_label.setText(f"{telemetry['speed']} km/h")
                self.rpm_card.value_label.setText(f"{telemetry['rpm']} RPM")
                self.gear_card.value_label.setText(str(telemetry["gear"]))

                for key in ("FL", "FR", "RL", "RR"):
                    surface = telemetry["tyres_surface"][key]
                    inner = telemetry["tyres_inner"][key]
                    self.tyre_labels[key]["surface"].setText(f"Surface: {surface}°C")
                    self.tyre_labels[key]["surface"].setStyleSheet(
                        f"color: {self.get_tyre_color(surface)};"
                    )
                    self.tyre_labels[key]["inner"].setText(f"Inner: {inner}°C")

                self.speed_graph.add_sample({"Speed": telemetry["speed"]}, now)
                self.rpm_graph.add_sample({"RPM": telemetry["rpm"]}, now)
                if now - getattr(self, "last_rpm_debug", 0) >= 1:
                    self.last_rpm_debug = now

                    print(
                        f"RPM from UDP: {telemetry['rpm']} | "
                        f"Graph points: {len(self.rpm_graph.times)}"
                    )
                
                self.tyre_graph.add_sample(telemetry["tyres_surface"], now)

        status = parse_car_status(data)
        if status is not None:
            self.data_logger.update_fuel(status["fuel"])
            self.fuel_card.value_label.setText(f"{status['fuel']:.1f} kg")
            if now - self.last_fuel_time >= 0.05:
                self.last_fuel_time = now
                self.fuel_graph.add_sample({"Fuel": status["fuel"]}, now)

    def update_graphs(self):
        for graph in (self.speed_graph, self.rpm_graph, self.fuel_graph, self.tyre_graph):
            graph.update_graph()

    def check_connection(self):
        active = (
            self.last_packet_time is not None
            and time.monotonic() - self.last_packet_time < 2
        )
        self.connection_label.setText("● UDP CONNECTED" if active else "● UDP DISCONNECTED")
        self.connection_label.setStyleSheet(
            "color: #22C55E;" if active else "color: #EF4444;"
        )

    def on_udp_error(self, error):
        print(f"UDP error: {error}")

    def closeEvent(self, event):
        self.data_logger.stop()
        self.connection_timer.stop()
        self.graph_timer.stop()
        self.udp_receiver.stop()
        event.accept()

    def apply_theme(self):
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
            QListWidget::item:hover { background-color: #292F3D; }
            QListWidget::item:selected {
                background-color: #C62828;
                color: white;
            }
            QLabel#pageTitle {
                background-color: transparent;
                font-size: 28px;
                font-weight: bold;
            }
            QFrame#telemetryCard, QFrame#tyrePanel {
                background-color: #1C2230;
                border: 1px solid #303849;
                border-radius: 12px;
            }
            QFrame#telemetryCard QLabel, QFrame#tyrePanel QLabel,
            QFrame#tyreCard QLabel {
                background-color: transparent;
                border: none;
            }
            QLabel#cardTitle, QLabel#tyreName {
                color: #98A2B3;
                font-size: 14px;
                font-weight: bold;
            }
            QLabel#cardValue {
                color: #FFFFFF;
                font-size: 38px;
                font-weight: bold;
            }
            QLabel#connectionStatus {
                background-color: transparent;
                color: #EF4444;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 0;
            }
            QFrame#tyreCard {
                background-color: #252C3B;
                border: 1px solid #394252;
                border-radius: 10px;
            }
            QLabel#tyreSurface {
                color: #FFFFFF;
                font-size: 19px;
                font-weight: bold;
            }
            QLabel#tyreInner {
                color: #AEB8C8;
                font-size: 15px;
            }
            QScrollArea { background-color: #101218; border: none; }
            QScrollBar:vertical {
                background-color: #181C25;
                width: 10px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #394252;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0px; }

            QPushButton {
                background-color: #252C3B;
                color: white;
                border: 1px solid #394252;
                border-radius: 8px;
                padding: 12px 18px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #394252;
            }
            QPushButton:disabled {
                color: #667085;
                background-color: #1C2230;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = F1Assistant()
    window.show()
    sys.exit(app.exec())
