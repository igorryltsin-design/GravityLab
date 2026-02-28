from __future__ import annotations

import sys
from dataclasses import dataclass
import re
from typing import Literal

from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QApplication


ThemeMode = Literal["day", "night"]

LEFT_PANEL_WIDTH = 248
RIGHT_PANEL_WIDTH = 248
WINDOW_WIDTH = 1560
WINDOW_HEIGHT = 940


@dataclass(frozen=True)
class ThemePalette:
    bg_top: str
    bg_bottom: str
    panel: str
    card: str
    card_alt: str
    border: str
    border_strong: str
    text: str
    text_muted: str
    accent: str
    accent_soft: str
    gold: str
    glow: str
    success: str
    menu_bg: str
    status_bg: str
    overlay_bg: str
    pill_bg: str
    button_bg: str
    button_hover: str
    button_pressed: str
    button_checked: str
    combo_bg: str
    slider_groove: str
    checkbox_bg: str
    canvas_top: str
    canvas_mid: str
    canvas_bottom: str
    canvas_nebula_left: str
    canvas_nebula_left_soft: str
    canvas_nebula_right: str
    canvas_nebula_right_soft: str
    canvas_star: str
    grid_minor: str
    grid_major: str
    clean_badge_bg: str
    clean_badge_border: str
    clean_badge_text: str
    label_connector: str
    label_bg: str
    label_bg_selected: str
    label_text: str
    label_text_selected: str
    spark_bg: str


DAY_PALETTE = ThemePalette(
    bg_top="#f3f9ff",
    bg_bottom="#dcecff",
    panel="rgba(255, 255, 255, 0.76)",
    card="rgba(255, 255, 255, 0.90)",
    card_alt="rgba(245, 250, 255, 0.96)",
    border="rgba(77, 128, 188, 0.22)",
    border_strong="rgba(77, 128, 188, 0.42)",
    text="#17304f",
    text_muted="#58779b",
    accent="#2e8fe8",
    accent_soft="rgba(46, 143, 232, 0.14)",
    gold="#d79a2b",
    glow="rgba(46, 143, 232, 0.12)",
    success="#2ca96b",
    menu_bg="rgba(247, 251, 255, 0.98)",
    status_bg="rgba(243, 248, 255, 0.95)",
    overlay_bg="rgba(255, 255, 255, 0.72)",
    pill_bg="rgba(243, 248, 255, 0.96)",
    button_bg="rgba(247, 251, 255, 0.98)",
    button_hover="rgba(233, 242, 252, 1.00)",
    button_pressed="rgba(223, 235, 249, 1.00)",
    button_checked="rgba(73, 144, 216, 0.92)",
    combo_bg="rgba(247, 251, 255, 0.98)",
    slider_groove="rgba(113, 147, 185, 0.24)",
    checkbox_bg="rgba(247, 251, 255, 0.98)",
    canvas_top="#edf7ff",
    canvas_mid="#d6ecff",
    canvas_bottom="#bddfff",
    canvas_nebula_left="rgba(142, 200, 255, 0.18)",
    canvas_nebula_left_soft="rgba(142, 200, 255, 0.06)",
    canvas_nebula_right="rgba(96, 163, 235, 0.22)",
    canvas_nebula_right_soft="rgba(96, 163, 235, 0.08)",
    canvas_star="#ffffff",
    grid_minor="rgba(83, 125, 172, 0.14)",
    grid_major="rgba(67, 104, 149, 0.28)",
    clean_badge_bg="rgba(255, 255, 255, 0.78)",
    clean_badge_border="rgba(88, 128, 174, 0.34)",
    clean_badge_text="#17304f",
    label_connector="rgba(72, 113, 158, 0.42)",
    label_bg="rgba(255, 255, 255, 0.84)",
    label_bg_selected="rgba(231, 244, 255, 0.95)",
    label_text="#17304f",
    label_text_selected="#0f2742",
    spark_bg="rgba(232, 242, 252, 0.92)",
)

NIGHT_PALETTE = ThemePalette(
    bg_top="#030914",
    bg_bottom="#0a1630",
    panel="rgba(7, 16, 30, 0.90)",
    card="rgba(12, 24, 46, 0.88)",
    card_alt="rgba(10, 20, 38, 0.95)",
    border="rgba(121, 163, 221, 0.22)",
    border_strong="rgba(121, 163, 221, 0.40)",
    text="#edf4ff",
    text_muted="#8ea6cb",
    accent="#6cbcff",
    accent_soft="rgba(108, 188, 255, 0.18)",
    gold="#ffd36e",
    glow="rgba(79, 131, 255, 0.20)",
    success="#8ee6b8",
    menu_bg="rgba(8, 16, 30, 0.98)",
    status_bg="rgba(6, 12, 22, 0.80)",
    overlay_bg="rgba(8, 16, 30, 0.78)",
    pill_bg="rgba(14, 26, 49, 0.90)",
    button_bg="rgba(14, 26, 49, 0.96)",
    button_hover="rgba(22, 39, 71, 0.98)",
    button_pressed="rgba(10, 20, 38, 0.98)",
    button_checked="rgba(48, 94, 158, 0.86)",
    combo_bg="rgba(10, 20, 38, 0.96)",
    slider_groove="rgba(58, 80, 112, 0.34)",
    checkbox_bg="rgba(10, 20, 38, 0.95)",
    canvas_top="#020913",
    canvas_mid="#030914",
    canvas_bottom="#0a1630",
    canvas_nebula_left="rgba(38, 76, 144, 0.19)",
    canvas_nebula_left_soft="rgba(15, 32, 64, 0.05)",
    canvas_nebula_right="rgba(54, 89, 150, 0.33)",
    canvas_nebula_right_soft="rgba(33, 66, 124, 0.13)",
    canvas_star="#ffffff",
    grid_minor="rgba(130, 161, 207, 0.07)",
    grid_major="rgba(182, 202, 235, 0.20)",
    clean_badge_bg="rgba(9, 17, 30, 0.72)",
    clean_badge_border="rgba(112, 147, 201, 0.28)",
    clean_badge_text="#edf4ff",
    label_connector="rgba(112, 147, 201, 0.43)",
    label_bg="rgba(7, 15, 27, 0.80)",
    label_bg_selected="rgba(7, 15, 27, 0.88)",
    label_text="#e7f0ff",
    label_text_selected="#ffffff",
    spark_bg="rgba(8, 15, 28, 0.74)",
)

_CURRENT_THEME_MODE: ThemeMode = "day"
PALETTE = DAY_PALETTE


def preferred_font_family() -> str:
    if sys.platform == "darwin":
        return "Helvetica Neue"
    if sys.platform.startswith("win"):
        return "Segoe UI"
    return "Helvetica Neue"


def title_font() -> QFont:
    font = QFont(preferred_font_family(), 16)
    font.setWeight(QFont.Weight.DemiBold)
    return font


def body_font() -> QFont:
    return QFont(preferred_font_family(), 10)


def mono_font() -> QFont:
    family = "SF Mono" if sys.platform == "darwin" else "Consolas"
    return QFont(family, 10)


def current_theme_mode() -> ThemeMode:
    return _CURRENT_THEME_MODE


def current_palette() -> ThemePalette:
    return PALETTE


def set_theme_mode(mode: ThemeMode) -> ThemePalette:
    global _CURRENT_THEME_MODE, PALETTE
    _CURRENT_THEME_MODE = mode
    PALETTE = NIGHT_PALETTE if mode == "night" else DAY_PALETTE
    return PALETTE


def accent_color(alpha: int = 255) -> QColor:
    color = qcolor(current_palette().accent)
    color.setAlpha(alpha)
    return color


def qcolor(value: str) -> QColor:
    color = QColor(value)
    if color.isValid():
        return color

    rgba_match = re.fullmatch(
        r"rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*([0-9]*\.?[0-9]+)\s*\)",
        value,
    )
    if rgba_match:
        red, green, blue, alpha = rgba_match.groups()
        alpha_value = float(alpha)
        if alpha_value <= 1.0:
            alpha_value *= 255.0
        return QColor(int(red), int(green), int(blue), max(0, min(255, int(round(alpha_value)))))

    rgb_match = re.fullmatch(r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)", value)
    if rgb_match:
        red, green, blue = rgb_match.groups()
        return QColor(int(red), int(green), int(blue))

    return QColor("#000000")


def build_stylesheet() -> str:
    palette = current_palette()
    return f"""
    QWidget {{
        color: {palette.text};
        background: transparent;
        font-family: "{preferred_font_family()}";
        font-size: 13px;
    }}
    QMainWindow {{
        background: qlineargradient(
            x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 {palette.bg_top}, stop: 1 {palette.bg_bottom}
        );
    }}
    QDialog {{
        background: qlineargradient(
            x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 {palette.bg_top}, stop: 1 {palette.bg_bottom}
        );
    }}
    QStatusBar {{
        background: {palette.status_bg};
        border-top: 1px solid {palette.border};
    }}
    QMenuBar {{
        background: {palette.menu_bg};
        border-bottom: 1px solid {palette.border};
    }}
    QMenuBar::item:selected, QMenu::item:selected {{
        background: {palette.accent_soft};
    }}
    QMenu {{
        background: {palette.menu_bg};
        border: 1px solid {palette.border};
    }}
    QFrame#panelShell {{
        background: {palette.panel};
        border: 1px solid {palette.border};
        border-radius: 24px;
    }}
    QFrame#metricCard {{
        background: qlineargradient(
            x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 {palette.card}, stop: 1 {palette.card_alt}
        );
        border: 1px solid {palette.border};
        border-radius: 18px;
    }}
    QFrame#panelDivider {{
        min-height: 1px;
        max-height: 1px;
        background: {palette.border};
        border: none;
        margin: 4px 0;
    }}
    QFrame#topBar, QFrame#bottomStrip {{
        background: {palette.overlay_bg};
        border: 1px solid {palette.border};
        border-radius: 18px;
    }}
    QLabel#eyebrow {{
        color: {palette.gold};
        font-size: 11px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}
    QLabel#overlayTitle {{
        font-size: 16px;
        font-weight: 650;
    }}
    QLabel#overlayPill {{
        background: {palette.pill_bg};
        border: 1px solid {palette.border};
        border-radius: 11px;
        padding: 6px 10px;
    }}
    QLabel#summaryBlock {{
        color: {palette.text};
        background: {palette.accent_soft};
        border: 1px solid {palette.border};
        border-radius: 14px;
        padding: 10px 12px;
    }}
    QLabel#dataBlock {{
        color: {palette.text};
        background: transparent;
    }}
    QLabel#mutedText {{
        color: {palette.text_muted};
    }}
    QLabel#sectionTitle {{
        font-size: 16px;
        font-weight: 650;
    }}
    QPushButton {{
        background: {palette.button_bg};
        border: 1px solid {palette.border};
        border-radius: 12px;
        padding: 9px 13px;
        min-height: 18px;
    }}
    QPushButton:hover {{
        background: {palette.button_hover};
        border-color: {palette.border_strong};
    }}
    QPushButton:pressed {{
        background: {palette.button_pressed};
    }}
    QPushButton:checked {{
        background: {palette.button_checked};
        border-color: {palette.border_strong};
    }}
    QPushButton#accentButton {{
        background: {palette.button_checked};
        border-color: {palette.border_strong};
        font-weight: 650;
    }}
    QPushButton#accentButton:hover {{
        background: {palette.accent};
    }}
    QComboBox, QToolBox::tab, QLineEdit {{
        background: {palette.combo_bg};
        border: 1px solid {palette.border};
        border-radius: 10px;
        padding: 8px 10px;
        min-height: 18px;
    }}
    QComboBox QAbstractItemView {{
        background: {palette.menu_bg};
        border: 1px solid {palette.border};
        selection-background-color: {palette.accent_soft};
    }}
    QTextBrowser, QTextEdit, QPlainTextEdit {{
        background: {palette.card_alt};
        color: {palette.text};
        border: 1px solid {palette.border};
        border-radius: 16px;
        padding: 12px;
        selection-background-color: {palette.accent_soft};
    }}
    QTabWidget::pane {{
        background: {palette.card_alt};
        border: 1px solid {palette.border};
        border-radius: 16px;
        top: -1px;
    }}
    QTabBar::tab {{
        background: {palette.combo_bg};
        color: {palette.text_muted};
        border: 1px solid {palette.border};
        border-bottom: none;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        padding: 8px 14px;
        margin-right: 6px;
    }}
    QTabBar::tab:selected {{
        background: {palette.card_alt};
        color: {palette.text};
        border-color: {palette.border_strong};
    }}
    QTabBar::tab:hover:!selected {{
        background: {palette.button_hover};
        color: {palette.text};
    }}
    QSlider::groove:horizontal {{
        height: 6px;
        background: {palette.slider_groove};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {palette.accent};
        border: 1px solid rgba(255,255,255,0.2);
        width: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }}
    QCheckBox {{
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 5px;
        border: 1px solid {palette.border};
        background: {palette.checkbox_bg};
    }}
    QCheckBox::indicator:checked {{
        background: {palette.accent};
    }}
    QScrollArea {{
        border: none;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 4px 0 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {palette.border_strong};
        border-radius: 5px;
        min-height: 28px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {palette.accent};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
        border: none;
        height: 0px;
    }}
    QToolTip {{
        background: {palette.card_alt};
        color: {palette.text};
        border: 1px solid {palette.border_strong};
        padding: 6px 8px;
        border-radius: 8px;
    }}
    QSplitter::handle {{
        background: transparent;
        width: 8px;
    }}
    QToolBox::tab {{
        margin-top: 8px;
        font-weight: 600;
    }}
    """


def apply_theme(app: QApplication, mode: ThemeMode | None = None) -> None:
    if mode is not None:
        set_theme_mode(mode)
    app.setStyle("Fusion")
    app.setStyleSheet(build_stylesheet())
