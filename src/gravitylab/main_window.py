from __future__ import annotations

from pathlib import Path
import time

from PyQt6.QtCore import QParallelAnimationGroup, QPropertyAnimation, QSettings, QTimer, Qt
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .sim.model import GravitySim
from .theme import LEFT_PANEL_WIDTH, RIGHT_PANEL_WIDTH, WINDOW_HEIGHT, WINDOW_WIDTH, ThemeMode, apply_theme, current_theme_mode
from .ui import BottomStrip, ControlPanel, HelpDialog, InspectorPanel, SimulationCanvas, TopBar


class MainWindow(QMainWindow):
    COMPACT_WIDTH = 1180
    NARROW_WIDTH = 980
    VERY_NARROW_WIDTH = 860
    COMPACT_HEIGHT = 980
    SHORT_HEIGHT = 820
    PANEL_REFRESH_INTERVAL = 0.12
    SNAPSHOT_TRAIL_POINTS = 420

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GravityLab")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        self.settings = QSettings()
        self.sim = GravitySim()
        self.canvas = SimulationCanvas()
        self.control_panel = ControlPanel()
        self.inspector_panel = InspectorPanel()
        self.info_panel = self.inspector_panel
        self.top_bar = TopBar()
        self.bottom_strip = BottomStrip()
        self._last_tick = time.perf_counter()
        self._last_panel_refresh = 0.0
        self.timer = QTimer(self)
        self._auto_hidden_controls = False
        self._auto_hidden_inspector = False
        self.theme_mode: ThemeMode = "day"
        self.help_dialog: HelpDialog | None = None

        self._build_layout()
        self._create_actions()
        self._connect_signals()
        self._setup_shortcuts()
        self._restore_settings()
        self._bootstrap_presets()
        self._animate_entry()
        self._start_timer()
        self._refresh_ui()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.timer.stop()
        if hasattr(self, "_entry_animation"):
            self._entry_animation.stop()
        self._save_settings()
        super().closeEvent(event)

    def _build_layout(self) -> None:
        self.control_panel.setMinimumWidth(220)
        self.control_panel.setMaximumWidth(280)
        self.control_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self.inspector_panel.setMinimumWidth(228)
        self.inspector_panel.setMaximumWidth(278)
        self.inspector_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        stage = QWidget()
        self.stage_layout = QVBoxLayout(stage)
        self.stage_layout.setContentsMargins(0, 0, 0, 0)
        self.stage_layout.setSpacing(10)
        self.stage_layout.addWidget(self.top_bar)
        self.stage_layout.addWidget(self.canvas, 1)
        self.stage_layout.addWidget(self.bottom_strip)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.control_panel)
        self.splitter.addWidget(stage)
        self.splitter.addWidget(self.inspector_panel)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)
        self.splitter.setSizes([LEFT_PANEL_WIDTH, 980, RIGHT_PANEL_WIDTH])

        shell = QWidget()
        self.shell_layout = QHBoxLayout(shell)
        self.shell_layout.setContentsMargins(16, 12, 12, 12)
        self.shell_layout.addWidget(self.splitter)
        self.setCentralWidget(shell)

        self.status_title = QLabel()
        self.statusBar().addPermanentWidget(self.status_title)
        self.statusBar().setSizeGripEnabled(False)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_responsive_layout()

    def _create_actions(self) -> None:
        self.file_menu = self.menuBar().addMenu("&Файл")
        self.view_menu = self.menuBar().addMenu("&Вид")
        self.sim_menu = self.menuBar().addMenu("&Симуляция")
        self.help_menu = self.menuBar().addMenu("&Справка")

        self.take_screenshot_action = QAction("Сделать снимок", self)
        self.take_screenshot_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.quit_action = QAction("Выход", self)
        self.quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.file_menu.addAction(self.take_screenshot_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.quit_action)

        self.toggle_controls_action = QAction("Показывать панель управления", self, checkable=True)
        self.toggle_controls_action.setChecked(True)
        self.toggle_info_action = QAction("Показывать инспектор", self, checkable=True)
        self.toggle_info_action.setChecked(True)
        self.clean_ui_action = QAction("Чистый UI", self, checkable=True)
        self.cinematic_action = QAction("Кино-камера", self, checkable=True)
        self.night_theme_action = QAction("Ночная тема", self, checkable=True)
        self.fit_action = QAction("Подогнать сцену", self)
        self.reset_view_action = QAction("Сбросить вид", self)
        self.view_menu.addAction(self.toggle_controls_action)
        self.view_menu.addAction(self.toggle_info_action)
        self.view_menu.addAction(self.clean_ui_action)
        self.view_menu.addAction(self.cinematic_action)
        self.view_menu.addAction(self.night_theme_action)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.fit_action)
        self.view_menu.addAction(self.reset_view_action)

        self.play_pause_action = QAction("Старт / Пауза", self)
        self.play_pause_action.setShortcut(QKeySequence(Qt.Key.Key_Space))
        self.step_action = QAction("Один шаг", self)
        self.step_action.setShortcut(QKeySequence("Ctrl+."))
        self.reset_action = QAction("Сбросить систему", self)
        self.reset_action.setShortcut(QKeySequence(Qt.Key.Key_R))
        self.next_body_action = QAction("Следующее тело", self)
        self.next_body_action.setShortcut(QKeySequence(Qt.Key.Key_Tab))
        self.sim_menu.addAction(self.play_pause_action)
        self.sim_menu.addAction(self.step_action)
        self.sim_menu.addAction(self.reset_action)
        self.sim_menu.addAction(self.next_body_action)

        self.about_action = QAction("О GravityLab", self)
        self.help_details_action = QAction("Подробная справка", self)
        self.help_menu.addAction(self.about_action)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.help_details_action)

    def _connect_signals(self) -> None:
        self.top_bar.play_pause_requested.connect(self._toggle_play_pause)
        self.top_bar.reset_requested.connect(lambda: self._reset_system(self.sim.num_planets))
        self.top_bar.fit_requested.connect(self.canvas.fit_to_scene)
        self.top_bar.screenshot_requested.connect(self._take_screenshot)
        self.top_bar.help_requested.connect(self._show_help_dialog)
        self.top_bar.theme_toggled.connect(self._set_night_theme_enabled)
        self.top_bar.clean_ui_toggled.connect(self._set_clean_ui)
        self.top_bar.cinematic_toggled.connect(self._set_cinematic_mode)
        self.top_bar.next_body_requested.connect(self._select_next_planet)

        self.bottom_strip.play_pause_requested.connect(self._toggle_play_pause)
        self.bottom_strip.step_requested.connect(self._step_once)
        self.bottom_strip.reset_requested.connect(lambda: self._reset_system(self.sim.num_planets))
        self.bottom_strip.time_scale_changed.connect(self._set_time_scale)

        self.control_panel.num_planets_changed.connect(self._reset_system)
        self.control_panel.gravity_changed.connect(self._set_g)
        self.control_panel.time_scale_changed.connect(self._set_time_scale)
        self.control_panel.asteroid_density_changed.connect(self._set_asteroid_belt_density)
        self.control_panel.mode_toggled.connect(self._set_mode)
        self.control_panel.preset_requested.connect(self._apply_named_preset)
        self.control_panel.fit_requested.connect(self.canvas.fit_to_scene)
        self.control_panel.reset_view_requested.connect(self._reset_view_manual)
        self.control_panel.screenshot_requested.connect(self._take_screenshot)

        self.inspector_panel.center_selected_requested.connect(self._center_on_selected)
        self.inspector_panel.follow_selected_toggled.connect(self._set_follow_selected)
        self.inspector_panel.speed_scaled.connect(self._scale_speed)
        self.inspector_panel.mass_scaled.connect(self._scale_mass)

        self.canvas.body_selected.connect(self._handle_canvas_selection)
        self.canvas.zoom_changed.connect(self._set_render_zoom)
        self.canvas.manual_camera_interacted.connect(self._disable_follow_for_manual_camera)

        self.take_screenshot_action.triggered.connect(self._take_screenshot)
        self.quit_action.triggered.connect(self.close)
        self.play_pause_action.triggered.connect(self._toggle_play_pause)
        self.step_action.triggered.connect(self._step_once)
        self.reset_action.triggered.connect(lambda: self._reset_system(self.sim.num_planets))
        self.next_body_action.triggered.connect(self._select_next_planet)
        self.fit_action.triggered.connect(self.canvas.fit_to_scene)
        self.reset_view_action.triggered.connect(self._reset_view_manual)
        self.toggle_controls_action.toggled.connect(self.control_panel.setVisible)
        self.toggle_info_action.toggled.connect(self.inspector_panel.setVisible)
        self.clean_ui_action.toggled.connect(self._set_clean_ui)
        self.cinematic_action.toggled.connect(self._set_cinematic_mode)
        self.night_theme_action.toggled.connect(self._set_night_theme_enabled)
        self.about_action.triggered.connect(self._show_about)
        self.help_details_action.triggered.connect(self._show_help_dialog)

    def _setup_shortcuts(self) -> None:
        for index in range(1, 10):
            shortcut = QShortcut(QKeySequence(str(index)), self)
            shortcut.activated.connect(lambda value=index: self._reset_system(value))

        for key, callback in (
            ("[", self._select_prev_planet),
            ("]", self._select_next_planet),
            ("-", lambda: self._scale_speed(0.9)),
            ("=", lambda: self._scale_speed(1.1)),
            ("PgUp", lambda: self._set_g(self.sim.g * 1.1)),
            ("PgDown", lambda: self._set_g(self.sim.g / 1.1)),
            ("O", lambda: self._toggle_mode_named("only_sun")),
            ("T", lambda: self._toggle_mode_named("trails")),
            ("G", lambda: self._toggle_mode_named("grid")),
            ("C", lambda: self._toggle_mode_named("theory")),
            ("L", lambda: self._toggle_mode_named("labels")),
            ("F", lambda: self._set_follow_selected(True)),
            ("U", lambda: self._set_clean_ui(not self.sim.render_options.clean_ui)),
            ("Escape", self.close),
        ):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)

    def _bootstrap_presets(self) -> None:
        presets = self.sim.preset_definitions()
        self.control_panel.set_presets(presets, self.sim.active_preset)
        self.top_bar.set_presets(presets)

    def _start_timer(self) -> None:
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start()

    def _on_tick(self) -> None:
        if not self.isVisible():
            return
        now = time.perf_counter()
        delta = max(1e-6, now - self._last_tick)
        self._last_tick = now
        self.sim.set_fps(1.0 / delta)
        if not self.sim.paused:
            self.sim.step()
        self._refresh_ui(force_panels=False)

    def _refresh_ui(self, force_panels: bool = True) -> None:
        snapshot = self.sim.snapshot(trail_points=self.SNAPSHOT_TRAIL_POINTS)
        stats = self.sim.stats()

        self.canvas.set_snapshot(snapshot)
        self.sim.set_render_zoom(self.canvas.zoom)
        self.top_bar.update_state(snapshot, stats)
        self.bottom_strip.update_state(snapshot, stats)
        self.play_pause_action.setText("Старт" if snapshot.paused else "Пауза")
        self.clean_ui_action.blockSignals(True)
        self.clean_ui_action.setChecked(snapshot.render_options.clean_ui)
        self.clean_ui_action.blockSignals(False)
        self.cinematic_action.blockSignals(True)
        self.cinematic_action.setChecked(snapshot.render_options.cinematic_mode)
        self.cinematic_action.blockSignals(False)
        self.status_title.setText(
            f"{'Пауза' if snapshot.paused else 'Live'} | {snapshot.active_preset or 'Без пресета'} | "
            f"тело {snapshot.bodies[snapshot.selected_index].name} | G {snapshot.g:.2f} | fps {stats.fps:.1f}"
        )
        self.top_bar.set_theme_mode(self.theme_mode == "night")

        now = time.perf_counter()
        if force_panels or now - self._last_panel_refresh >= self.PANEL_REFRESH_INTERVAL:
            self._refresh_panels(snapshot, stats)
            self._last_panel_refresh = now

    def _refresh_panels(self, snapshot, stats) -> None:
        series = self.sim.selected_body_series()
        self.control_panel.update_state(snapshot, stats, self.sim.config, self.sim.render_options)
        self.inspector_panel.update_state(snapshot, stats, series)
        self._sync_panel_visibility()
        self._apply_responsive_layout()

    def _sync_panel_visibility(self) -> None:
        if self.sim.render_options.clean_ui:
            self.control_panel.hide()
            self.inspector_panel.hide()
            return
        self.control_panel.setVisible(self.toggle_controls_action.isChecked())
        self.inspector_panel.setVisible(self.toggle_info_action.isChecked())

    def _apply_responsive_layout(self) -> None:
        width = self.width()
        height = self.height()
        compact = width < self.COMPACT_WIDTH or height < self.COMPACT_HEIGHT
        narrow = width < self.NARROW_WIDTH
        very_narrow = width < self.VERY_NARROW_WIDTH
        short = height < self.SHORT_HEIGHT

        self.top_bar.set_compact_mode(compact)
        self.top_bar.set_short_mode(short)
        self.bottom_strip.set_compact_mode(compact)
        self.bottom_strip.set_short_mode(short)
        self.control_panel.set_compact_mode(compact)
        self.control_panel.set_short_mode(short)
        self.inspector_panel.set_compact_mode(compact)
        self.inspector_panel.set_short_mode(short)
        self.stage_layout.setSpacing(6 if compact else 10)
        self.shell_layout.setContentsMargins(10 if compact else 16, 8 if compact else 12, 8 if compact else 12, 8 if compact else 12)
        self.statusBar().setVisible(not short)

        if self.sim.render_options.clean_ui:
            return

        if very_narrow:
            self._auto_hidden_controls = True
            self._auto_hidden_inspector = True
            self.control_panel.hide()
            self.inspector_panel.hide()
        elif narrow:
            self._auto_hidden_controls = False
            self._auto_hidden_inspector = True
            self.control_panel.setVisible(self.toggle_controls_action.isChecked())
            self.inspector_panel.hide()
        else:
            self._auto_hidden_controls = False
            self._auto_hidden_inspector = False
            self.control_panel.setVisible(self.toggle_controls_action.isChecked())
            self.inspector_panel.setVisible(self.toggle_info_action.isChecked())

        if very_narrow:
            self.splitter.setSizes([0, max(320, width - 24), 0])
        elif narrow:
            self.splitter.setSizes([200 if self.control_panel.isVisible() else 0, max(380, width - 240), 0])
        elif compact:
            self.splitter.setSizes([
                210 if self.control_panel.isVisible() else 0,
                max(520, width - 470),
                240 if self.inspector_panel.isVisible() else 0,
            ])
        else:
            self.splitter.setSizes([
                LEFT_PANEL_WIDTH if self.control_panel.isVisible() else 0,
                max(640, width - LEFT_PANEL_WIDTH - RIGHT_PANEL_WIDTH - 40),
                RIGHT_PANEL_WIDTH if self.inspector_panel.isVisible() else 0,
            ])

    def _toggle_play_pause(self) -> None:
        self.sim.toggle_mode("paused")
        self._refresh_ui()

    def _step_once(self) -> None:
        self.sim.step()
        self._refresh_ui()

    def _reset_system(self, planets: int) -> None:
        self.sim.reset_system(planets)
        self.canvas.fit_to_scene()
        self._refresh_ui()

    def _apply_named_preset(self, preset_id: str) -> None:
        was_paused = self.sim.paused
        self.sim.apply_named_preset(preset_id)
        self.sim.paused = was_paused
        self.canvas.fit_to_scene()
        self.toggle_info_action.setChecked(True)
        self._refresh_ui()

    def _set_g(self, value: float) -> None:
        self.sim.set_g(value)
        self._refresh_ui()

    def _set_time_scale(self, value: float) -> None:
        self.sim.set_time_scale(value)
        self._refresh_ui()

    def _set_mode(self, mode: str, enabled: bool) -> None:
        self.sim.set_mode(mode, enabled)
        self._refresh_ui()

    def _set_asteroid_belt_density(self, count: int) -> None:
        self.sim.set_asteroid_belt_density(count)
        self._refresh_ui()

    def _toggle_mode_named(self, mode: str) -> None:
        self.sim.toggle_mode(mode)
        self._refresh_ui()

    def _set_selected_planet(self, index: int) -> None:
        self.sim.set_selected_planet(index)
        self._refresh_ui()

    def _handle_canvas_selection(self, index: int) -> None:
        self._set_selected_planet(index)
        if not self.sim.render_options.clean_ui:
            self.toggle_info_action.setChecked(True)
            self._sync_panel_visibility()

    def _select_prev_planet(self) -> None:
        current = self.sim.selected_planet_idx - 1
        if current < 1:
            current = self.sim.num_planets
        self._set_selected_planet(current)

    def _select_next_planet(self) -> None:
        current = self.sim.selected_planet_idx + 1
        if current > self.sim.num_planets:
            current = 1
        self._set_selected_planet(current)

    def _scale_speed(self, factor: float) -> None:
        self.sim.set_speed_scale_for_selected(factor)
        self._refresh_ui()

    def _scale_mass(self, factor: float) -> None:
        self.sim.set_mass_scale_for_selected(factor)
        self._refresh_ui()

    def _center_on_selected(self) -> None:
        self.canvas.center_on_body_index(self.sim.selected_planet_idx)
        self._refresh_ui()

    def _set_follow_selected(self, enabled: bool) -> None:
        if enabled:
            self.sim.set_follow_target(self.sim.selected_planet_idx)
            self.sim.set_cinematic_mode(True)
        else:
            self.sim.set_follow_target(None)
        self._refresh_ui()

    def _set_cinematic_mode(self, enabled: bool) -> None:
        self.sim.set_cinematic_mode(enabled)
        self._refresh_ui()

    def _disable_follow_for_manual_camera(self) -> None:
        if self.sim.render_options.cinematic_mode and self.sim.follow_target_index is not None:
            self.sim.set_follow_target(None)
            self.sim.set_camera_mode("manual")
            self._refresh_ui()

    def _set_clean_ui(self, enabled: bool) -> None:
        self.sim.set_clean_ui(enabled)
        self._sync_panel_visibility()
        self._refresh_ui()

    def _reset_view_manual(self) -> None:
        self.sim.set_camera_mode("manual")
        self.sim.set_follow_target(None)
        self.canvas.reset_view()
        self._refresh_ui()

    def _set_render_zoom(self, zoom: float) -> None:
        self.sim.set_render_zoom(zoom)
        self._refresh_ui()

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "О GravityLab",
            "GravityLab — это canvas-first демонстрационная песочница гравитации на PyQt6.\n\n"
            "Она сочетает учебную модель задачи N-тел с режимами камеры, демо-пресетами, overlays и компактной аналитикой.",
        )

    def _show_help_dialog(self) -> None:
        if self.help_dialog is None:
            self.help_dialog = HelpDialog(self.sim.preset_definitions(), self)
        self.help_dialog.show()
        self.help_dialog.raise_()
        self.help_dialog.activateWindow()

    def _set_night_theme_enabled(self, enabled: bool) -> None:
        self._set_theme_mode("night" if enabled else "day")

    def _set_theme_mode(self, mode: ThemeMode) -> None:
        self.theme_mode = mode
        app = QApplication.instance()
        if app is not None:
            apply_theme(app, mode)
        night_enabled = mode == "night"
        self.night_theme_action.blockSignals(True)
        self.night_theme_action.setChecked(night_enabled)
        self.night_theme_action.blockSignals(False)
        self.top_bar.set_theme_mode(night_enabled)
        self.canvas.update()
        self.inspector_panel.update()

    def _take_screenshot(self) -> None:
        default_name = Path.cwd() / "gravitylab-screenshot.png"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить снимок",
            str(default_name),
            "Изображения PNG (*.png)",
        )
        if not path:
            return
        if not self.canvas.export_screenshot(path):
            QMessageBox.warning(self, "Не удалось сохранить снимок", "Не получилось записать PNG-файл.")

    def _animate_entry(self) -> None:
        group = QParallelAnimationGroup(self)
        for widget in (self.control_panel, self.top_bar, self.bottom_strip, self.inspector_panel):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
            animation = QPropertyAnimation(effect, b"opacity", self)
            animation.setDuration(520)
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
            group.addAnimation(animation)
        group.start()
        self._entry_animation = group

    def _restore_settings(self) -> None:
        geometry = self.settings.value("window/geometry")
        splitter_state = self.settings.value("window/splitter_state")
        if geometry is not None:
            self.restoreGeometry(geometry)
        if splitter_state is not None:
            self.splitter.restoreState(splitter_state)

        self.toggle_controls_action.setChecked(self.settings.value("view/control_visible", True, bool))
        self.toggle_info_action.setChecked(True)
        self.sim.render_options.show_grid = self.settings.value("render/show_grid", True, bool)
        self.sim.render_options.show_trails = self.settings.value("render/show_trails", True, bool)
        self.sim.render_options.show_theory = self.settings.value("render/show_theory", False, bool)
        self.sim.render_options.show_labels = self.settings.value("render/show_labels", True, bool)
        self.sim.render_options.show_sparklines = self.settings.value("render/show_sparklines", True, bool)
        self.sim.render_options.clean_ui = self.settings.value("render/clean_ui", False, bool)
        self.sim.render_options.cinematic_mode = self.settings.value("render/cinematic_mode", False, bool)
        self.sim.only_sun = self.settings.value("render/only_sun", False, bool)
        self.sim.asteroid_belt_count = self.settings.value(
            "render/asteroid_belt_count",
            self.sim.asteroid_belt_count,
            int,
        )
        asteroid_belt_enabled = self.settings.value("render/asteroid_belt_enabled", False, bool)
        self.sim.set_asteroid_belt_enabled(asteroid_belt_enabled)
        self.sim.render_options.zoom = float(self.settings.value("render/zoom", 1.0))
        self.theme_mode = self.settings.value("theme/mode", current_theme_mode(), str)
        self._set_theme_mode("night" if self.theme_mode == "night" else "day")
        self._sync_panel_visibility()

    def _save_settings(self) -> None:
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("window/splitter_state", self.splitter.saveState())
        self.settings.setValue("view/control_visible", self.toggle_controls_action.isChecked())
        self.settings.setValue("view/info_visible", self.toggle_info_action.isChecked())
        self.settings.setValue("render/show_grid", self.sim.render_options.show_grid)
        self.settings.setValue("render/show_trails", self.sim.render_options.show_trails)
        self.settings.setValue("render/show_theory", self.sim.render_options.show_theory)
        self.settings.setValue("render/show_labels", self.sim.render_options.show_labels)
        self.settings.setValue("render/show_sparklines", self.sim.render_options.show_sparklines)
        self.settings.setValue("render/clean_ui", self.sim.render_options.clean_ui)
        self.settings.setValue("render/cinematic_mode", self.sim.render_options.cinematic_mode)
        self.settings.setValue("render/only_sun", self.sim.only_sun)
        self.settings.setValue("render/asteroid_belt_enabled", self.sim.asteroid_belt_enabled)
        self.settings.setValue("render/asteroid_belt_count", self.sim.asteroid_belt_count)
        self.settings.setValue("render/zoom", self.sim.render_options.zoom)
        self.settings.setValue("theme/mode", self.theme_mode)
