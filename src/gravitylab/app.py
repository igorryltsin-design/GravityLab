from __future__ import annotations

import os
import sys
from pathlib import Path

import PyQt6
from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow
from .theme import apply_theme


def configure_qt_environment() -> None:
    # В собранном (PyInstaller) приложении пути к Qt уже настроены рантаймом.
    # Повторная установка переменной окружения может сломать поиск плагинов на macOS.
    if getattr(sys, "frozen", False):
        return
    plugin_dir = Path(PyQt6.__file__).resolve().parent / "Qt6" / "plugins" / "platforms"
    if plugin_dir.exists():
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(plugin_dir))


def create_application(argv: list[str] | None = None) -> QApplication:
    configure_qt_environment()
    app = QApplication(argv or sys.argv)
    # Эти поля использует QSettings и ОС для идентификации приложения.
    app.setOrganizationName("GravityLab")
    app.setApplicationName("GravityLab")
    app.setApplicationDisplayName("GravityLab")
    # Применяем глобальную тему до создания главного окна.
    apply_theme(app)
    return app


def run(argv: list[str] | None = None) -> int:
    app = create_application(argv)
    # Главное окно связывает симуляцию и все UI-компоненты.
    window = MainWindow()
    window.show()
    return app.exec()
