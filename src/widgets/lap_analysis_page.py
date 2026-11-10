
import csv
from pathlib import Path
import sys

import pyqtgraph as pg

from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from analysis.session_analyzer import SessionAnalyzer


class LapAnalysisPage(QWidget):
    """Страница анализа сохранённых CSV-сессий."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.analyzer = None

        # Прокручиваемая область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("Lap Analysis")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # Панель выбора CSV
        file_row = QHBoxLayout()

        self.open_button = QPushButton("Open CSV")
        self.open_button.clicked.connect(self.open_csv)

        self.file_label = QLabel("No session selected")
        self.file_label.setWordWrap(True)

        file_row.addWidget(self.open_button)
        file_row.addWidget(self.file_label, 1)

        layout.addLayout(file_row)

        # Карточки статистики
        stats_grid = QGridLayout()
        stats_grid.setSpacing(15)

        self.stats_labels = {}

        stats = [
            ("max_speed", "MAX SPEED", "km/h"),
            ("avg_speed", "AVG SPEED", "km/h"),
            ("max_rpm", "MAX RPM", "RPM"),
            ("duration", "DURATION", "s"),
            ("samples", "SAMPLES", ""),
            ("fuel_start", "START FUEL", "kg"),
            ("fuel_end", "END FUEL", "kg"),
        ]

        for index, (key, name, unit) in enumerate(stats):

            card = QFrame()
            card.setObjectName("analysisCard")

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 15, 18, 15)

            name_label = QLabel(name)
            name_label.setObjectName("analysisCardTitle")

            value_label = QLabel("--")
            value_label.setObjectName("analysisCardValue")

            card_layout.addWidget(name_label)
            card_layout.addWidget(value_label)

            self.stats_labels[key] = (value_label, unit)

            stats_grid.addWidget(
                card, index // 3, index % 3
            )

        layout.addLayout(stats_grid)

        # График скорости
        self.speed_plot, self.speed_curves = (
            self.create_plot(
                "RECORDED SPEED",
                "Speed",
                "km/h",
                {"Speed": "#EF4444"},
            )
        )

        # График оборотов двигателя
        self.rpm_plot, self.rpm_curves = (
            self.create_plot(
                "ENGINE RPM",
                "RPM",
                "RPM",
                {"RPM": "#3B82F6"},
            )
        )

        # График топлива
        self.fuel_plot, self.fuel_curves = (
            self.create_plot(
                "FUEL LEVEL",
                "Fuel",
                "kg",
                {"Fuel": "#F59E0B"},
            )
        )

        # График температуры поверхности четырёх шин
        self.tyre_plot, self.tyre_curves = (
            self.create_plot(
                "TYRE SURFACE TEMPERATURE",
                "Temperature",
                "°C",
                {
                    "FL": "#22C55E",
                    "FR": "#F97316",
                    "RL": "#38BDF8",
                    "RR": "#A78BFA",
                },
            )
        )

        for plot in (
            self.speed_plot,
            self.rpm_plot,
            self.fuel_plot,
            self.tyre_plot,
        ):
            layout.addWidget(plot)

        layout.addStretch()

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        self.apply_page_style()

    def create_plot(self, title, label, unit, series):
        """Создаёт график с одной или несколькими линиями."""

        plot = pg.PlotWidget()
        plot.setBackground("#1C2230")

        plot.setTitle(
            title,
            color="#FFFFFF",
            size="13pt"
        )

        plot.setLabel("bottom", "Time", units="s")
        plot.setLabel("left", label, units=unit)

        plot.showGrid(
            x=True,
            y=True,
            alpha=0.2
        )

        plot.setMinimumHeight(280)

        # Добавляем легенду до создания линий
        if len(series) > 1:
            plot.addLegend(offset=(10, 10))

        curves = {}

        for name, color in series.items():
            curves[name] = plot.plot(
                name=name,
                pen=pg.mkPen(
                    color=color,
                    width=2
                )
            )

        return plot, curves

    def open_csv(self):
        """Загружает CSV и обновляет интерфейс."""

        # Для собранного EXE используем папку приложения
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).resolve().parent
        else:
            base_dir = Path(__file__).resolve().parents[2]

        initial_dir = base_dir / "data" / "sessions"

        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select F1 Telemetry CSV",
            str(initial_dir if initial_dir.exists() else base_dir),
            "CSV files (*.csv)"
        )

        if not filepath:
            return

        analyzer = SessionAnalyzer(filepath)

        try:
            count = analyzer.load()
            stats = analyzer.get_statistics()

        except (OSError, UnicodeError, csv.Error) as error:
            QMessageBox.warning(
                self,
                "CSV Error",
                str(error)
            )
            return

        if count == 0 or stats is None:
            QMessageBox.warning(
                self,
                "No Data",
                "CSV contains no valid telemetry samples."
            )
            return

        self.analyzer = analyzer
        self.file_label.setText(Path(filepath).name)

        # Отображаем рассчитанную статистику
        for key, (label, unit) in self.stats_labels.items():
            value = stats[key]

            if value is None:
                text = "--"
            elif key in ("samples", "max_rpm"):
                text = f"{value:.0f}"
            else:
                text = f"{value:.1f}"

            label.setText(
                f"{text} {unit}".strip()
                if value is not None else "--"
            )

        # Подключаем данные к графикам
        self.set_curve(
            self.speed_curves["Speed"], "speed"
        )

        self.set_curve(
            self.rpm_curves["RPM"], "rpm"
        )

        self.set_curve(
            self.fuel_curves["Fuel"], "fuel"
        )

        for tyre in ("FL", "FR", "RL", "RR"):
            self.set_curve(
                self.tyre_curves[tyre],
                f"tyre_{tyre.lower()}"
            )

        # Пересчитываем границы осей
        for plot in (
            self.speed_plot,
            self.rpm_plot,
            self.fuel_plot,
            self.tyre_plot,
        ):
            plot.enableAutoRange(
                x=True,
                y=True
            )

    def set_curve(self, curve, key):
        """Передаёт записанные значения в линию графика."""

        times, values = self.analyzer.get_series(key)

        curve.setData(times, values)

    def apply_page_style(self):
        """Оформление карточек анализа."""

        self.setStyleSheet("""
            QFrame#analysisCard {
                background-color: #1C2230;
                border: 1px solid #303849;
                border-radius: 12px;
            }

            QFrame#analysisCard QLabel {
                background-color: transparent;
                border: none;
            }

            QLabel#analysisCardTitle {
                color: #98A2B3;
                font-size: 13px;
                font-weight: bold;
            }

            QLabel#analysisCardValue {
                color: white;
                font-size: 28px;
                font-weight: bold;
            }
        """)
