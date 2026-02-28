from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..sim.model import BodySeriesSnapshot, SimulationSnapshot, SimulationStats
from ..theme import current_palette, qcolor


class Sparkline(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._values: tuple[float, ...] = ()
        self._color = QColor("#6cbcff")
        self.setMinimumHeight(54)

    def set_series(self, values: tuple[float, ...], color: QColor | None = None) -> None:
        self._values = values
        if color is not None:
            self._color = color
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), qcolor(current_palette().spark_bg))
        if len(self._values) < 2:
            painter.end()
            return

        minimum = min(self._values)
        maximum = max(self._values)
        spread = maximum - minimum or 1.0
        points = []
        for index, value in enumerate(self._values):
            x = 8 + (self.width() - 16) * index / max(1, len(self._values) - 1)
            y = 8 + (self.height() - 16) * (1.0 - (value - minimum) / spread)
            points.append(QPointF(x, y))
        painter.setPen(QPen(self._color, 2))
        for index in range(1, len(points)):
            painter.drawLine(points[index - 1], points[index])
        painter.end()


class InspectorPanel(QWidget):
    center_selected_requested = pyqtSignal()
    follow_selected_toggled = pyqtSignal(bool)
    speed_scaled = pyqtSignal(float)
    mass_scaled = pyqtSignal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._compact_mode = False
        self._short_mode = False
        self._show_theory = True
        self._show_sparklines = True
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        shell = QFrame()
        shell.setObjectName("panelShell")
        self._shell_layout = QVBoxLayout(shell)
        self._shell_layout.setContentsMargins(10, 10, 10, 10)
        self._shell_layout.setSpacing(10)

        self.selected_card = self._metric_card("Выбранное тело")
        self.selected_title = self.selected_card.layout().itemAt(0).widget()
        self.selected_label = QLabel()
        self.selected_label.setObjectName("dataBlock")
        self.selected_label.setWordWrap(True)
        self.selected_card.layout().addWidget(self.selected_label)
        self._shell_layout.addWidget(self.selected_card)

        self.actions_card = self._metric_card("Быстрые действия")
        actions_layout = self.actions_card.layout()
        first_row = QHBoxLayout()
        self.center_button = QPushButton("Центрировать")
        self.follow_checkbox = QCheckBox("Следовать")
        first_row.addWidget(self.center_button)
        first_row.addWidget(self.follow_checkbox)
        second_row = QHBoxLayout()
        self.slow_button = QPushButton("-10%")
        self.fast_button = QPushButton("+10%")
        second_row.addWidget(self.slow_button)
        second_row.addWidget(self.fast_button)
        third_row = QHBoxLayout()
        self.mass_down_button = QPushButton("Масса -10%")
        self.mass_up_button = QPushButton("Масса +10%")
        third_row.addWidget(self.mass_down_button)
        third_row.addWidget(self.mass_up_button)
        actions_layout.addLayout(first_row)
        actions_layout.addLayout(second_row)
        actions_layout.addLayout(third_row)
        self._shell_layout.addWidget(self.actions_card)

        self.metrics_card = self._metric_card("Метрики")
        self.metrics_label = QLabel()
        self.metrics_label.setObjectName("dataBlock")
        self.metrics_label.setWordWrap(True)
        self.metrics_card.layout().addWidget(self.metrics_label)
        self._shell_layout.addWidget(self.metrics_card)

        self.sparklines_card = self._metric_card("История")
        spark_layout = self.sparklines_card.layout()
        self.distance_caption = QLabel("Расстояние")
        self.distance_caption.setObjectName("mutedText")
        self.distance_spark = Sparkline()
        self.speed_caption = QLabel("Скорость")
        self.speed_caption.setObjectName("mutedText")
        self.speed_spark = Sparkline()
        spark_layout.addWidget(self.distance_caption)
        spark_layout.addWidget(self.distance_spark)
        spark_layout.addWidget(self.speed_caption)
        spark_layout.addWidget(self.speed_spark)
        self._shell_layout.addWidget(self.sparklines_card)

        self.theory_card = self._metric_card("Теория")
        self.theory_label = QLabel(self._theory_text())
        self.theory_label.setObjectName("mutedText")
        self.theory_label.setWordWrap(True)
        self.theory_card.layout().addWidget(self.theory_label)
        self._shell_layout.addWidget(self.theory_card)
        self._shell_layout.addStretch(1)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(shell)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll_area)

        self._apply_tooltips()
        self.center_button.clicked.connect(self.center_selected_requested.emit)
        self.follow_checkbox.toggled.connect(self.follow_selected_toggled.emit)
        self.slow_button.clicked.connect(lambda: self.speed_scaled.emit(0.9))
        self.fast_button.clicked.connect(lambda: self.speed_scaled.emit(1.1))
        self.mass_down_button.clicked.connect(lambda: self.mass_scaled.emit(0.9))
        self.mass_up_button.clicked.connect(lambda: self.mass_scaled.emit(1.1))

    def set_compact_mode(self, compact: bool) -> None:
        self._compact_mode = compact
        self.setMinimumWidth(206 if compact else 228)
        self.setMaximumWidth(246 if compact else 278)
        self._shell_layout.setContentsMargins(8 if compact else 10, 8 if compact else 10, 8 if compact else 10, 8 if compact else 10)
        self._shell_layout.setSpacing(8 if compact else 10)
        self._set_card_density(compact)
        self._update_secondary_visibility()

    def set_short_mode(self, short: bool) -> None:
        self._short_mode = short
        if short:
            self.follow_checkbox.setText("")
        else:
            self.follow_checkbox.setText("Следовать")
        self._update_secondary_visibility()

    def update_state(
        self,
        snapshot: SimulationSnapshot,
        stats: SimulationStats,
        series: BodySeriesSnapshot,
    ) -> None:
        selected = snapshot.bodies[snapshot.selected_index]
        speed = math.hypot(selected.vx, selected.vy)
        distance = math.hypot(selected.x - snapshot.bodies[0].x, selected.y - snapshot.bodies[0].y)
        angle = math.degrees(math.atan2(selected.y, selected.x))

        self.selected_title.setText(f"{selected.name}")
        self.selected_label.setText(
            "\n".join(
                [
                    f"Индекс: {selected.index}",
                    f"Координаты: ({selected.x:.1f}, {selected.y:.1f})",
                    f"Масса: {self._format_mass(selected.mass)}",
                    f"Скорость: {speed:.2f}",
                    f"Радиус орбиты: {distance:.1f} ед.",
                    f"Угол: {angle:.1f}°",
                ]
            )
        )
        self.metrics_label.setText(
            "\n".join(
                [
                    f"FPS: {stats.fps:.1f}",
                    f"G: {snapshot.g:.2f}",
                    f"Время: {stats.sim_time:.2f} c",
                    f"Камера: {self._camera_mode_label(snapshot.camera_mode)}",
                    f"Пресет: {snapshot.active_preset or 'нет'}",
                ]
            )
        )
        self.follow_checkbox.blockSignals(True)
        self.follow_checkbox.setChecked(snapshot.follow_target_index == selected.index)
        self.follow_checkbox.blockSignals(False)
        self._show_sparklines = snapshot.render_options.show_sparklines
        self._show_theory = snapshot.render_options.show_theory
        self.distance_spark.set_series(series.distance_history, QColor("#6cbcff"))
        self.speed_spark.set_series(series.speed_history, QColor("#ffd36e"))
        self._update_secondary_visibility()

    def _metric_card(self, title: str) -> QFrame:
        card = QFrame()
        card.setObjectName("metricCard")
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        header = QLabel(title)
        header.setObjectName("sectionTitle")
        header.setWordWrap(True)
        layout.addWidget(header)
        return card

    def _set_card_density(self, compact: bool) -> None:
        margins = 8 if compact else 10
        spacing = 5 if compact else 6
        for card in (self.selected_card, self.actions_card, self.metrics_card, self.sparklines_card, self.theory_card):
            layout = card.layout()
            layout.setContentsMargins(margins, margins, margins, margins)
            layout.setSpacing(spacing)

    def _update_secondary_visibility(self) -> None:
        allow_extras = not self._compact_mode and not self._short_mode
        self.sparklines_card.setVisible(self._show_sparklines and allow_extras)
        self.theory_card.setVisible(self._show_theory and allow_extras)

    def _theory_text(self) -> str:
        return (
            "Орбитальная скорость:\n"
            "v = sqrt(G * M / r)\n\n"
            "Если увеличить скорость, орбита вытягивается.\n"
            "Если уменьшить скорость, тело уходит ближе к Солнцу.\n\n"
            "Подробная теория, описание программы и пресетов находятся в окне «Справка»."
        )

    def _camera_mode_label(self, mode: str) -> str:
        labels = {
            "manual": "ручная",
            "follow_selected": "следовать за телом",
            "follow_sun": "следовать за Солнцем",
            "auto_frame": "авто-кадр",
        }
        return labels.get(mode, mode)

    def _apply_tooltips(self) -> None:
        self.selected_card.setToolTip("Параметры выбранного тела: положение, масса, скорость и орбитальный радиус.")
        self.actions_card.setToolTip("Быстрые действия для выбранного тела.")
        self.metrics_card.setToolTip("Ключевые показатели сцены и камеры.")
        self.sparklines_card.setToolTip("История изменения расстояния и скорости выбранного тела.")
        self.theory_card.setToolTip("Краткая физическая памятка. Полная версия находится в окне справки.")
        self.center_button.setToolTip("Центрирует камеру на выбранном теле.")
        self.follow_checkbox.setToolTip("Закрепляет камеру за выбранным телом.")
        self.slow_button.setToolTip("Уменьшает скорость выбранного тела на 10%.")
        self.fast_button.setToolTip("Увеличивает скорость выбранного тела на 10%.")
        self.mass_down_button.setToolTip("Уменьшает массу выбранного тела на 10%.")
        self.mass_up_button.setToolTip("Увеличивает массу выбранного тела на 10%.")

    def _format_mass(self, mass: float) -> str:
        if mass >= 1000.0:
            return f"{mass:,.0f} M⊕".replace(",", " ")
        if mass >= 10.0:
            return f"{mass:.1f} M⊕"
        if mass >= 1.0:
            return f"{mass:.2f} M⊕"
        return f"{mass:.4f} M⊕"
