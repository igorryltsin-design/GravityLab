from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..sim.model import PresetDefinition


class PresetBrowser(QWidget):
    preset_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.preset_combo = QComboBox()
        self.description_label = QLabel()
        self.description_label.setObjectName("mutedText")
        self.description_label.setWordWrap(True)
        self.apply_button = QPushButton("Применить пресет")

        layout.addWidget(self.preset_combo)
        layout.addWidget(self.description_label)
        layout.addWidget(self.apply_button)

        self._apply_tooltips()
        self.preset_combo.currentIndexChanged.connect(self._update_description)
        self.apply_button.clicked.connect(self._emit_requested)

    def set_presets(self, presets: tuple[PresetDefinition, ...], active_label: str | None = None) -> None:
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        for preset in presets:
            self.preset_combo.addItem(preset.label, preset)
        if active_label:
            for index in range(self.preset_combo.count()):
                preset = self.preset_combo.itemData(index)
                if preset and preset.label == active_label:
                    self.preset_combo.setCurrentIndex(index)
                    break
        self.preset_combo.blockSignals(False)
        self._update_description()

    def _emit_requested(self) -> None:
        preset = self.current_preset()
        if preset is not None:
            self.preset_requested.emit(preset.id)

    def current_preset(self) -> PresetDefinition | None:
        return self.preset_combo.currentData()

    def _update_description(self) -> None:
        preset = self.current_preset()
        self.description_label.setText("" if preset is None else preset.description)

    def _apply_tooltips(self) -> None:
        self.preset_combo.setToolTip("Список готовых сцен для демонстрации разных режимов орбит и камеры.")
        self.description_label.setToolTip("Краткое описание того, что показывает выбранный пресет.")
        self.apply_button.setToolTip("Применяет выбранную сцену и её начальные параметры.")
