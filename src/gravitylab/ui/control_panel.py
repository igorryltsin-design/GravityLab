from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QFrame, QLabel, QScrollArea, QSlider, QVBoxLayout, QWidget

from ..sim.model import PresetDefinition, RenderOptions, SimulationConfig, SimulationSnapshot, SimulationStats
from .preset_browser import PresetBrowser


class ControlPanel(QWidget):
    num_planets_changed = pyqtSignal(int)
    gravity_changed = pyqtSignal(float)
    time_scale_changed = pyqtSignal(float)
    asteroid_density_changed = pyqtSignal(int)
    mode_toggled = pyqtSignal(str, bool)
    preset_requested = pyqtSignal(str)
    fit_requested = pyqtSignal()
    reset_view_requested = pyqtSignal()
    screenshot_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._compact_mode = False
        self._short_mode = False
        self.setMinimumWidth(220)
        self.setMaximumWidth(280)

        shell = QFrame()
        shell.setObjectName("panelShell")
        self._shell_layout = QVBoxLayout(shell)
        self._shell_layout.setContentsMargins(14, 14, 14, 14)
        self._shell_layout.setSpacing(12)

        self.eyebrow = QLabel("Панель сцены")
        self.eyebrow.setObjectName("eyebrow")
        self.title_label = QLabel("Все настройки сцены")
        self.title_label.setObjectName("sectionTitle")
        self._shell_layout.addWidget(self.eyebrow)
        self._shell_layout.addWidget(self.title_label)

        self.settings_card = self._build_settings_card()
        self._shell_layout.addWidget(self.settings_card)
        self._shell_layout.addStretch(1)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(shell)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll_area)

        self._apply_tooltips()
        self._connect_signals()

    def set_compact_mode(self, compact: bool) -> None:
        self._compact_mode = compact
        self.setMinimumWidth(188 if compact else 220)
        self.setMaximumWidth(236 if compact else 280)
        self._shell_layout.setContentsMargins(10 if compact else 14, 10 if compact else 14, 10 if compact else 14, 10 if compact else 14)
        self._shell_layout.setSpacing(8 if compact else 12)
        self._settings_layout.setContentsMargins(10 if compact else 14, 10 if compact else 14, 10 if compact else 14, 10 if compact else 14)
        self._settings_layout.setSpacing(8 if compact else 10)

    def set_short_mode(self, short: bool) -> None:
        self._short_mode = short
        self.eyebrow.setVisible(not short)
        self.title_label.setVisible(not short)
        self.preset_browser.description_label.setVisible(not short)

    def set_presets(self, presets: tuple[PresetDefinition, ...], active_label: str | None = None) -> None:
        self.preset_browser.set_presets(presets, active_label)

    def update_state(
        self,
        snapshot: SimulationSnapshot,
        stats: SimulationStats,
        _config: SimulationConfig,
        render_options: RenderOptions,
    ) -> None:
        self._set_slider(self.planet_slider, snapshot.num_planets)
        self._set_slider(self.gravity_slider, int(round(snapshot.g * 100)))
        self._set_slider(self.time_scale_slider, int(round(snapshot.time_scale * 100)))
        self._set_slider(self.asteroid_density_slider, snapshot.asteroid_belt_count)
        self.planet_value.setText(f"{snapshot.num_planets} тел")
        self.gravity_value.setText(f"{snapshot.g:.2f}")
        self.time_scale_value.setText(f"{snapshot.time_scale:.2f}x")
        self.asteroid_density_value.setText(f"{snapshot.asteroid_belt_count} астероидов")
        self.summary_label.setText(
            "<b>Текущая сцена</b><br>"
            f"{snapshot.active_preset or 'Свободная сцена'}<br><br>"
            f"<b>Выбрано тело</b><br>{snapshot.bodies[snapshot.selected_index].name}<br><br>"
            f"<b>FPS</b><br>{stats.fps:.1f}"
        )

        self._set_checkbox(self.trails_checkbox, render_options.show_trails)
        self._set_checkbox(self.grid_checkbox, render_options.show_grid)
        self._set_checkbox(self.labels_checkbox, render_options.show_labels)
        self._set_checkbox(self.theory_checkbox, render_options.show_theory)
        self._set_checkbox(self.only_sun_checkbox, snapshot.only_sun)
        self._set_checkbox(self.asteroid_belt_checkbox, snapshot.asteroid_belt_enabled)

    def _build_settings_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("metricCard")
        self._settings_layout = QVBoxLayout(card)
        self._settings_layout.setContentsMargins(14, 14, 14, 14)
        self._settings_layout.setSpacing(10)

        self.summary_label = QLabel()
        self.summary_label.setObjectName("summaryBlock")
        self.summary_label.setTextFormat(Qt.TextFormat.RichText)
        self.summary_label.setWordWrap(True)
        self._settings_layout.addWidget(self.summary_label)

        self.planet_slider = self._slider(1, 9)
        self.gravity_slider = self._slider(1, 1200)
        self.time_scale_slider = self._slider(10, 2400)
        self.asteroid_density_slider = self._slider(0, 240)
        self.planet_value = QLabel()
        self.gravity_value = QLabel()
        self.time_scale_value = QLabel()
        self.asteroid_density_value = QLabel()

        for title, slider, value in (
            ("Планеты", self.planet_slider, self.planet_value),
            ("Гравитация G", self.gravity_slider, self.gravity_value),
            ("Масштаб времени", self.time_scale_slider, self.time_scale_value),
            ("Плотность пояса", self.asteroid_density_slider, self.asteroid_density_value),
        ):
            self._add_field(title, slider, value)

        self._add_separator()

        self.trails_checkbox = QCheckBox("Следы")
        self.grid_checkbox = QCheckBox("Сетка")
        self.labels_checkbox = QCheckBox("Подписи")
        self.theory_checkbox = QCheckBox("Теория")
        self.only_sun_checkbox = QCheckBox("Только притяжение Солнца")
        self.asteroid_belt_checkbox = QCheckBox("Пояс астероидов")
        for checkbox in (
            self.trails_checkbox,
            self.grid_checkbox,
            self.labels_checkbox,
            self.theory_checkbox,
            self.only_sun_checkbox,
            self.asteroid_belt_checkbox,
        ):
            self._settings_layout.addWidget(checkbox)

        self._add_separator()

        preset_label = QLabel("Пресеты")
        preset_label.setObjectName("mutedText")
        self.preset_browser = PresetBrowser()
        self._settings_layout.addWidget(preset_label)
        self._settings_layout.addWidget(self.preset_browser)
        return card

    def _add_field(self, title: str, slider: QSlider, value: QLabel) -> None:
        label = QLabel(title)
        label.setObjectName("mutedText")
        self._settings_layout.addWidget(label)
        self._settings_layout.addWidget(slider)
        self._settings_layout.addWidget(value)

    def _add_separator(self) -> None:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("panelDivider")
        self._settings_layout.addWidget(line)

    def _apply_tooltips(self) -> None:
        self.planet_slider.setToolTip("Меняет число основных планет в сцене от 1 до 9.")
        self.gravity_slider.setToolTip("Условная сила притяжения G. Больше значение — сильнее гравитация.")
        self.time_scale_slider.setToolTip("Ускоряет или замедляет ход симуляции без изменения структуры сцены.")
        self.asteroid_density_slider.setToolTip("Определяет, сколько астероидов будет в поясе при включённом режиме.")

        self.trails_checkbox.setToolTip("Показывает хвосты траекторий, чтобы было видно форму орбит.")
        self.grid_checkbox.setToolTip("Включает вспомогательную сетку на сцене.")
        self.labels_checkbox.setToolTip("Показывает подписи планет рядом с телами на сцене.")
        self.theory_checkbox.setToolTip("Показывает компактный блок с формулами и пояснениями справа.")
        self.only_sun_checkbox.setToolTip(
            "Тела притягиваются только к Солнцу. Взаимное влияние планет и астероидов друг на друга отключается."
        )
        self.asteroid_belt_checkbox.setToolTip(
            "Добавляет пояс астероидов. По умолчанию он размещается внутри системы, а в пресете «Солнечная система» — между Марсом и Юпитером."
        )

        self.preset_browser.preset_combo.setToolTip("Выбор готового сценария сцены.")
        self.preset_browser.apply_button.setToolTip("Применяет выбранный пресет с его стартовыми параметрами.")

    def _connect_signals(self) -> None:
        self.planet_slider.valueChanged.connect(self.num_planets_changed.emit)
        self.gravity_slider.valueChanged.connect(lambda value: self.gravity_changed.emit(value / 100.0))
        self.time_scale_slider.valueChanged.connect(lambda value: self.time_scale_changed.emit(value / 100.0))
        self.asteroid_density_slider.valueChanged.connect(self.asteroid_density_changed.emit)
        self.trails_checkbox.toggled.connect(lambda checked: self.mode_toggled.emit("trails", checked))
        self.grid_checkbox.toggled.connect(lambda checked: self.mode_toggled.emit("grid", checked))
        self.labels_checkbox.toggled.connect(lambda checked: self.mode_toggled.emit("labels", checked))
        self.theory_checkbox.toggled.connect(lambda checked: self.mode_toggled.emit("theory", checked))
        self.only_sun_checkbox.toggled.connect(lambda checked: self.mode_toggled.emit("only_sun", checked))
        self.asteroid_belt_checkbox.toggled.connect(lambda checked: self.mode_toggled.emit("asteroid_belt", checked))
        self.preset_browser.preset_requested.connect(self.preset_requested.emit)

    def _slider(self, minimum: int, maximum: int) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        return slider

    def _set_slider(self, slider: QSlider, value: int) -> None:
        slider.blockSignals(True)
        slider.setValue(value)
        slider.blockSignals(False)

    def _set_checkbox(self, checkbox: QCheckBox, value: bool) -> None:
        checkbox.blockSignals(True)
        checkbox.setChecked(value)
        checkbox.blockSignals(False)
