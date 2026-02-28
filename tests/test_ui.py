from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import QScrollArea, QTextBrowser

from gravitylab.main_window import MainWindow


def test_main_window_opens(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    assert window.windowTitle() == "GravityLab"
    assert window.canvas is not None


def test_play_pause_and_step_update_state(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    window.top_bar.play_pause_button.click()
    assert window.sim.paused is True

    steps_before = window.sim.step_count
    window.bottom_strip.step_button.click()
    assert window.sim.step_count == steps_before + 1


def test_gravity_slider_updates_model(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    window.control_panel.gravity_slider.setValue(350)
    assert window.sim.g == 3.5
    assert "3.50" in window.status_title.text()


def test_next_body_button_changes_selection(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    initial_index = window.sim.selected_planet_idx
    window.top_bar.next_body_button.click()
    expected = initial_index + 1
    if expected > window.sim.num_planets:
        expected = 1
    assert window.sim.selected_planet_idx == expected


def test_canvas_click_selects_planet(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window._refresh_ui()

    target = window.canvas.body_screen_point(1)
    qtbot.mouseClick(window.canvas, Qt.MouseButton.LeftButton, pos=target)
    assert window.sim.selected_planet_idx == 1


def test_inspector_is_visible_by_default(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1400, 900)
    window.show()
    assert window.info_panel.isVisible() is True


def test_theme_mode_persists(qtbot, tmp_path):
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))

    first = MainWindow()
    first.show()
    first.top_bar.theme_button.click()
    assert first.theme_mode == "night"
    first.close()

    second = MainWindow()
    qtbot.addWidget(second)
    second.show()
    assert second.theme_mode == "night"
    assert second.night_theme_action.isChecked() is True


def test_clean_ui_hides_side_panels(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    window.top_bar.clean_ui_button.click()
    assert window.control_panel.isVisible() is False
    assert window.info_panel.isVisible() is False


def test_preset_selection_updates_scene(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    index = window.control_panel.preset_browser.preset_combo.findText("Спираль к Солнцу")
    window.control_panel.preset_browser.preset_combo.setCurrentIndex(index)
    window.control_panel.preset_browser.apply_button.click()
    assert window.sim.snapshot().active_preset == "Спираль к Солнцу"


def test_follow_selected_can_be_enabled(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    window.inspector_panel.follow_checkbox.setChecked(True)
    assert window.sim.follow_target_index == window.sim.selected_planet_idx


def test_mass_buttons_update_selected_body_mass(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    initial_mass = window.sim.selected_body().mass
    window.inspector_panel.mass_up_button.click()
    assert window.sim.selected_body().mass > initial_mass
    window.inspector_panel.mass_down_button.click()
    assert window.sim.selected_body().mass < initial_mass * 1.1


def test_theory_toggle_hides_inspector_theory_card(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1400, 1100)
    window.show()
    window._set_mode("theory", True)
    window._refresh_ui()
    qtbot.wait(20)
    assert window.sim.render_options.show_theory is True
    assert window.inspector_panel.theory_card.isHidden() is False
    window.control_panel.theory_checkbox.setChecked(False)
    window._refresh_ui()
    qtbot.wait(20)
    assert window.sim.render_options.show_theory is False
    assert window.inspector_panel.theory_card.isHidden() is True


def test_help_button_opens_help_dialog(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.top_bar.help_button.click()
    assert window.help_dialog is not None
    assert window.help_dialog.isVisible() is True


def test_help_dialog_shows_author_block(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.top_bar.help_button.click()
    assert "Рыльцин Тимур" in window.help_dialog.author_label.text()


def test_help_dialog_presets_tab_is_scrollable(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.top_bar.help_button.click()
    presets_tab = window.help_dialog.tabs.widget(2)
    assert isinstance(presets_tab, QScrollArea)


def test_help_dialog_contains_extended_sections(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.top_bar.help_button.click()
    browsers = window.help_dialog.findChildren(QTextBrowser)
    texts = "\n".join(browser.toPlainText() for browser in browsers)
    assert "Что делает GravityLab" in texts
    assert "Физическая модель" in texts
    assert "Управление и навигация" in texts


def test_asteroid_belt_checkbox_adds_bodies(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    base_body_count = len(window.sim.bodies)
    window.control_panel.asteroid_belt_checkbox.setChecked(True)
    assert window.sim.snapshot().asteroid_belt_enabled is True
    assert len(window.sim.bodies) > base_body_count


def test_only_sun_checkbox_updates_model(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.control_panel.only_sun_checkbox.setChecked(True)
    assert window.sim.only_sun is True
    window.control_panel.only_sun_checkbox.setChecked(False)
    assert window.sim.only_sun is False


def test_only_sun_checkbox_has_explanatory_tooltip(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    assert "Взаимное влияние планет" in window.control_panel.only_sun_checkbox.toolTip()


def test_asteroid_density_slider_updates_model(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.control_panel.asteroid_density_slider.setValue(144)
    assert window.sim.asteroid_belt_count == 144


def test_solar_system_preset_turns_on_asteroid_belt(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    index = window.control_panel.preset_browser.preset_combo.findText("Солнечная система")
    window.control_panel.preset_browser.preset_combo.setCurrentIndex(index)
    window.control_panel.preset_browser.apply_button.click()
    assert window.sim.snapshot().active_preset == "Солнечная система"
    assert window.sim.snapshot().asteroid_belt_enabled is True


def test_narrow_window_hides_inspector(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.toggle_info_action.setChecked(True)
    window.resize(940, 800)
    qtbot.wait(20)
    assert window.info_panel.isVisible() is False


def test_very_narrow_window_hides_side_panels(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.toggle_info_action.setChecked(True)
    window.resize(820, 760)
    qtbot.wait(20)
    assert window.control_panel.isVisible() is False
    assert window.info_panel.isVisible() is False


def test_short_window_uses_compact_height_mode(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.toggle_info_action.setChecked(True)
    window.resize(1400, 780)
    qtbot.wait(20)
    assert window.statusBar().isVisible() is False
    assert window.top_bar.scene_label.isVisible() is False
    assert window.inspector_panel.theory_card.isVisible() is False
    assert window.inspector_panel.sparklines_card.isVisible() is False


def test_compact_height_tightens_control_panel(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.resize(1400, 900)
    qtbot.wait(20)
    assert window.control_panel.eyebrow.isVisible() is False
    assert window.bottom_strip.step_button.isVisible() is False


def test_time_scale_can_be_set_to_fast_value_from_bottom_strip(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    index = window.bottom_strip.time_scale_combo.findData(24.0)
    window.bottom_strip.time_scale_combo.setCurrentIndex(index)
    assert window.sim.time_scale == 24.0


def test_theme_toggle_updates_main_window_state(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    initial_mode = window.theme_mode
    assert window.top_bar.theme_button.text().startswith("Тема")
    window.top_bar.theme_button.click()
    assert window.theme_mode != initial_mode
    window.top_bar.theme_button.click()
    assert window.theme_mode == initial_mode
