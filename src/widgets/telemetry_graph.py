from collections import deque
import time

import pyqtgraph as pg
from PySide6.QtWidgets import QVBoxLayout, QWidget


class TelemetryGraph(QWidget):
    """График одной или нескольких величин за последние N секунд."""

    def __init__(self, title, series, duration=30, parent=None):
        super().__init__(parent)
        self.duration = duration
        self.start_time = time.monotonic()
        self.times = deque()
        self.series = {name: deque() for name in series}

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#1C2230")
        self.plot_widget.setTitle(title, color="#FFFFFF", size="13pt")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.setLabel("bottom", "Time", units="s")
        self.plot_widget.setMinimumHeight(210)

        self.curves = {}
        for name, color in series.items():
            self.curves[name] = self.plot_widget.plot(
                name=name,
                pen=pg.mkPen(color=color, width=2),
            )

        if len(series) > 1:
            self.plot_widget.addLegend(offset=(10, 10))
            # addLegend вызываем до plot() для автоматического заполнения;
            # существующие линии добавляем вручную.
            legend = self.plot_widget.plotItem.legend
            for name, curve in self.curves.items():
                legend.addItem(curve, name)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot_widget)

    def add_sample(self, values, timestamp=None):
        """Добавляет значения всех серий одним измерением."""
        timestamp = time.monotonic() if timestamp is None else timestamp
        elapsed = timestamp - self.start_time

        self.times.append(elapsed)
        for name, samples in self.series.items():
            samples.append(float(values[name]))

        self._trim(elapsed)

    def _trim(self, latest):
        """Сохраняет только последние duration секунд."""
        while self.times and latest - self.times[0] > self.duration:
            self.times.popleft()
            for samples in self.series.values():
                samples.popleft()

    def update_graph(self):
        """Перерисовывает линии; вызывается не чаще 20 раз/с."""
        if not self.times:
            return

        self._trim(time.monotonic() - self.start_time)
        if not self.times:
            return

        x_values = list(self.times)
        for name, curve in self.curves.items():
            curve.setData(x_values, list(self.series[name]))

        last = x_values[-1]
        self.plot_widget.setXRange(max(0, last - self.duration), max(self.duration, last), padding=0)
