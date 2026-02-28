from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from ..sim.model import PresetDefinition, SimulationSnapshot, SimulationStats


class TopBar(QWidget):
    play_pause_requested = pyqtSignal()
    reset_requested = pyqtSignal()
    fit_requested = pyqtSignal()
    screenshot_requested = pyqtSignal()
    help_requested = pyqtSignal()
    clean_ui_toggled = pyqtSignal(bool)
    cinematic_toggled = pyqtSignal(bool)
    theme_toggled = pyqtSignal(bool)
    next_body_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._compact_mode = False
        self._short_mode = False
        shell = QFrame()
        shell.setObjectName("topBar")

        self._shell_layout = QHBoxLayout(shell)
        self._shell_layout.setContentsMargins(16, 10, 16, 10)
        self._shell_layout.setSpacing(10)

        self.scene_label = QLabel("GravityLab")
        self.scene_label.setObjectName("overlayTitle")
        self.state_label = QLabel()
        self.state_label.setObjectName("overlayPill")
        self.zoom_label = QLabel()
        self.zoom_label.setObjectName("overlayPill")
        self.gravity_label = QLabel()
        self.gravity_label.setObjectName("overlayPill")

        self.next_body_button = QPushButton("Следующее тело")
        self.play_pause_button = QPushButton("Пауза")
        self.play_pause_button.setObjectName("accentButton")
        self.reset_button = QPushButton("Сброс")
        self.fit_button = QPushButton("Подогнать")
        self.screenshot_button = QPushButton("Снимок")
        self.help_button = QPushButton("Справка")
        self.theme_button = QPushButton("День")
        self.theme_button.setCheckable(True)
        self.clean_ui_button = QPushButton("Чистый UI")
        self.clean_ui_button.setCheckable(True)
        self.cinematic_button = QPushButton("Кино-камера")
        self.cinematic_button.setCheckable(True)

        self._shell_layout.addWidget(self.scene_label)
        self._shell_layout.addStretch(1)
        self._shell_layout.addWidget(self.state_label)
        self._shell_layout.addWidget(self.zoom_label)
        self._shell_layout.addWidget(self.gravity_label)
        self._shell_layout.addWidget(self.next_body_button)
        self._shell_layout.addWidget(self.play_pause_button)
        self._shell_layout.addWidget(self.reset_button)
        self._shell_layout.addWidget(self.fit_button)
        self._shell_layout.addWidget(self.screenshot_button)
        self._shell_layout.addWidget(self.help_button)
        self._shell_layout.addWidget(self.theme_button)
        self._shell_layout.addWidget(self.clean_ui_button)
        self._shell_layout.addWidget(self.cinematic_button)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)

        self._apply_tooltips()
        self.play_pause_button.clicked.connect(self.play_pause_requested.emit)
        self.reset_button.clicked.connect(self.reset_requested.emit)
        self.fit_button.clicked.connect(self.fit_requested.emit)
        self.screenshot_button.clicked.connect(self.screenshot_requested.emit)
        self.help_button.clicked.connect(self.help_requested.emit)
        self.next_body_button.clicked.connect(self.next_body_requested.emit)
        self.theme_button.toggled.connect(self._emit_theme_toggled)
        self.clean_ui_button.toggled.connect(self.clean_ui_toggled.emit)
        self.cinematic_button.toggled.connect(self.cinematic_toggled.emit)

    def set_compact_mode(self, compact: bool) -> None:
        self._compact_mode = compact
        self.next_body_button.setVisible(not compact)
        for button, compact_text, full_text in (
            (self.fit_button, "Fit", "Подогнать"),
            (self.screenshot_button, "PNG", "Снимок"),
            (self.help_button, "?", "Справка"),
            (self.clean_ui_button, "UI", "Чистый UI"),
            (self.cinematic_button, "Кино", "Кино-камера"),
        ):
            button.setText(compact_text if compact else full_text)
        self.scene_label.setMaximumWidth(220 if compact else 420)
        self.state_label.setVisible(not compact)
        self._shell_layout.setContentsMargins(12 if compact else 16, 6 if compact else 10, 12 if compact else 16, 6 if compact else 10)
        self._shell_layout.setSpacing(8 if compact else 10)
        self.set_theme_mode(self.theme_button.isChecked())

    def set_short_mode(self, short: bool) -> None:
        self._short_mode = short
        self.reset_button.setVisible(not short)
        self.screenshot_button.setVisible(not short)
        self.help_button.setVisible(not short)
        self.scene_label.setVisible(not short)

    def set_presets(self, presets: tuple[PresetDefinition, ...]) -> None:
        _ = presets

    def update_state(self, snapshot: SimulationSnapshot, stats: SimulationStats) -> None:
        _ = stats
        self.scene_label.setText(snapshot.active_preset or "Свободная сцена")
        self.state_label.setText("Пауза" if snapshot.paused else "В работе")
        self.zoom_label.setText(
            f"{'Z' if self._compact_mode else 'Масштаб'} {snapshot.render_options.zoom:.2f}x"
        )
        self.gravity_label.setText(f"G {snapshot.g:.2f}")
        self.play_pause_button.setText("Старт" if snapshot.paused else "Пауза")
        self.clean_ui_button.blockSignals(True)
        self.clean_ui_button.setChecked(snapshot.render_options.clean_ui)
        self.clean_ui_button.blockSignals(False)
        self.cinematic_button.blockSignals(True)
        self.cinematic_button.setChecked(snapshot.render_options.cinematic_mode)
        self.cinematic_button.blockSignals(False)

    def set_theme_mode(self, night_enabled: bool) -> None:
        self.theme_button.blockSignals(True)
        self.theme_button.setChecked(night_enabled)
        self.theme_button.setText("Тема: Ночь" if night_enabled else "Тема: День")
        self.theme_button.blockSignals(False)
        if self._compact_mode:
            self.theme_button.setText("Тема")

    def _emit_theme_toggled(self, checked: bool) -> None:
        self.set_theme_mode(checked)
        self.theme_toggled.emit(checked)

    def _apply_tooltips(self) -> None:
        self.scene_label.setToolTip("Имя текущего пресета или свободной сцены.")
        self.state_label.setToolTip("Текущее состояние симуляции: идёт расчёт или включена пауза.")
        self.zoom_label.setToolTip("Текущий масштаб сцены.")
        self.gravity_label.setToolTip("Текущее значение силы притяжения G.")
        self.next_body_button.setToolTip("Переключает выбор на следующее основное тело.")
        self.play_pause_button.setToolTip("Запускает или ставит симуляцию на паузу.")
        self.reset_button.setToolTip("Сбрасывает сцену к текущему числу планет или активному пресету.")
        self.fit_button.setToolTip("Подгоняет камеру так, чтобы вся система поместилась в кадр.")
        self.screenshot_button.setToolTip("Сохраняет текущий кадр сцены в PNG.")
        self.help_button.setToolTip("Открывает подробную справку по программе, физике и пресетам.")
        self.theme_button.setToolTip("Переключает дневную и ночную тему интерфейса.")
        self.clean_ui_button.setToolTip("Скрывает боковые панели и оставляет только сцену с overlays.")
        self.cinematic_button.setToolTip("Включает плавное следование камеры за выбранным телом.")
