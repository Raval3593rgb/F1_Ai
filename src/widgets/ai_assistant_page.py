
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
)


class AIAssistantPage(QWidget):
    """Интерфейс интеллектуального помощника F1."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Создаём прокручиваемую страницу
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(20)

        # Заголовок страницы
        title = QLabel("AI Assistant")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Intelligent telemetry analysis and driving recommendations"
        )
        subtitle.setStyleSheet("color: #98A2B3;")
        layout.addWidget(subtitle)

        # Информация о состоянии ИИ
        self.status_label = QLabel("AI STATUS: READY")
        self.status_label.setStyleSheet(
            "color: #22C55E; font-weight: bold;"
        )
        layout.addWidget(self.status_label)

        # Карточка состояния автомобиля
        vehicle_card, vehicle_layout = self.create_card(
            "VEHICLE HEALTH"
        )

        self.vehicle_status = QLabel(
            "Waiting for telemetry analysis..."
        )
        vehicle_layout.addWidget(self.vehicle_status)

        layout.addWidget(vehicle_card)

        # Карточка рекомендаций
        insights_card, insights_layout = self.create_card(
            "AI INSIGHTS"
        )

        self.insights_label = QLabel(
            "No recommendations yet. "
            "Run an analysis to get started."
        )
        self.insights_label.setWordWrap(True)
        insights_layout.addWidget(self.insights_label)

        layout.addWidget(insights_card)

        # Кнопка анализа
        button_row = QHBoxLayout()

        self.analyze_button = QPushButton("Analyze Session")
        self.analyze_button.setMinimumHeight(42)

        button_row.addWidget(self.analyze_button)
        button_row.addStretch()

        layout.addLayout(button_row)

        # Карточка ML-модуля
        ml_card, ml_layout = self.create_card(
            "MACHINE LEARNING"
        )

        self.ml_status = QLabel(
            "ML model: Not trained\n"
            "Training dataset: Not loaded"
        )
        ml_layout.addWidget(self.ml_status)

        layout.addWidget(ml_card)
        layout.addStretch()

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # Оформление карточек
        self.setStyleSheet("""
            QFrame#aiCard {
                background-color: #1C2230;
                border: 1px solid #303849;
                border-radius: 12px;
            }

            QLabel#aiCardTitle {
                color: #98A2B3;
                font-size: 13px;
                font-weight: bold;
            }

            QLabel#aiCardText {
                color: white;
                font-size: 15px;
            }
        """)

    def create_card(self, title):
        """Создаёт карточку с заголовком."""

        card = QFrame()
        card.setObjectName("aiCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("aiCardTitle")

        card_layout.addWidget(title_label)

        return card, card_layout
