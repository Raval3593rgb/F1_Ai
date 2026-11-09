
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
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

    def create_page(self, page_name):
        """Создаёт временную страницу с заголовком."""
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel(page_name)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("pageTitle")

        layout.addWidget(title)

        return page

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
        """)


if __name__ == "__main__":
    # QApplication управляет жизненным циклом GUI
    app = QApplication(sys.argv)

    window = F1Assistant()
    window.show()

    # Запускаем цикл обработки событий приложения
    sys.exit(app.exec())
