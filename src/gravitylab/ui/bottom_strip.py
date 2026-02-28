from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from ..sim.model import SimulationSnapshot, SimulationStats


class BottomStrip(QWidget):
    play_pause_requested = pyqtSignal()
    step_requested = pyqtSignal()
    reset_requested = pyqtSignal()
    time_scale_changed = pyqtSignal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._compact_mode = False
        self._short_mode = False
        shell = QFrame()
        shell.setObjectName("bottomStrip")
        self._shell_layout = QHBoxLayout(shell)
        self._shell_layout.setContentsMargins(16, 10, 16, 10)
        self._shell_layout.setSpacing(12)

        self.play_pause_button = QPushButton("Пауза")
        self.play_pause_button.setObjectName("accentButton")
        self.step_button = QPushButton("Шаг")
        self.reset_button = QPushButton("Сброс")
        self.time_scale_combo = QComboBox()
        for value in (0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 10.0, 16.0, 24.0):
            self.time_scale_combo.addItem(f"{value:.2f}x", value)

        self.sim_time_label = QLabel()
        self.selected_label = QLabel()
        self.distance_label = QLabel()
        self.preset_label = QLabel()
        for widget in (self.sim_time_label, self.selected_label, self.distance_label, self.preset_label):
            widget.setObjectName("overlayPill")

        self._shell_layout.addWidget(self.play_pause_button)
        self._shell_layout.addWidget(self.step_button)
        self._shell_layout.addWidget(self.reset_button)
        self._shell_layout.addWidget(self.time_scale_combo)
        self._shell_layout.addStretch(1)
        self._shell_layout.addWidget(self.sim_time_label)
        self._shell_layout.addWidget(self.selected_label)
        self._shell_layout.addWidget(self.distance_label)
        self._shell_layout.addWidget(self.preset_label)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)

        self._apply_tooltips()
        self.play_pause_button.clicked.connect(self.play_pause_requested.emit)
        self.step_button.clicked.connect(self.step_requested.emit)
        self.reset_button.clicked.connect(self.reset_requested.emit)
        self.time_scale_combo.currentIndexChanged.connect(self._emit_time_scale_changed)

    def set_compact_mode(self, compact: bool) -> None:
        self._compact_mode = compact
        self.step_button.setVisible(not compact)
        self.reset_button.setVisible(not compact)
        self.preset_label.setVisible(not compact)
        self.selected_label.setVisible(not compact)
        self.distance_label.setVisible(not compact)
        self.time_scale_combo.setMinimumWidth(90 if compact else 120)
        self.play_pause_button.setText("Старт" if compact else self.play_pause_button.text())
        self._shell_layout.setContentsMargins(12 if compact else 16, 6 if compact else 10, 12 if compact else 16, 6 if compact else 10)
        self._shell_layout.setSpacing(8 if compact else 12)

    def set_short_mode(self, short: bool) -> None:
        self._short_mode = short
        self.step_button.setVisible(not short and not self._compact_mode)
        self.reset_button.setVisible(not short and not self._compact_mode)
        self.selected_label.setVisible(not short and not self._compact_mode)
        self.distance_label.setVisible(not short and not self._compact_mode)
        self.preset_label.setVisible(not short and not self._compact_mode)
        self.sim_time_label.setVisible(True)

    def update_state(self, snapshot: SimulationSnapshot, stats: SimulationStats) -> None:
        selected = snapshot.bodies[snapshot.selected_index]
        self.play_pause_button.setText("Старт" if snapshot.paused else "Пауза")

        self.time_scale_combo.blockSignals(True)
        if self.time_scale_combo.findData(snapshot.time_scale) < 0:
            self.time_scale_combo.addItem(f"{snapshot.time_scale:.2f}x", snapshot.time_scale)
        for index in range(self.time_scale_combo.count()):
            if abs(float(self.time_scale_combo.itemData(index)) - snapshot.time_scale) < 1e-9:
                self.time_scale_combo.setCurrentIndex(index)
                break
        self.time_scale_combo.blockSignals(False)

        self.sim_time_label.setText(f"Время {stats.sim_time:.1f} c")
        self.selected_label.setText(f"Тело {selected.name}")
        self.distance_label.setText(f"Орбита {stats.selected_radius:.1f} ед.")
        self.preset_label.setText(snapshot.active_preset or "Без пресета")

    def _emit_time_scale_changed(self) -> None:
        value = self.time_scale_combo.currentData()
        if value is not None:
            self.time_scale_changed.emit(float(value))

    def _apply_tooltips(self) -> None:
        self.play_pause_button.setToolTip("Запускает или ставит симуляцию на паузу.")
        self.step_button.setToolTip("Выполняет один шаг расчёта, даже если включена пауза.")
        self.reset_button.setToolTip("Сбрасывает текущую сцену.")
        self.time_scale_combo.setToolTip("Выбор готового масштаба времени для ускорения или замедления симуляции.")
        self.sim_time_label.setToolTip("Сколько симуляционного времени прошло с начала сцены.")
        self.selected_label.setToolTip("Текущее выбранное тело.")
        self.distance_label.setToolTip("Расстояние выбранного тела до Солнца.")
        self.preset_label.setToolTip("Название активного пресета.")
