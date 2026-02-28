import os
from pathlib import Path

import PyQt6

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_API", "pyqt6")

plugin_dir = Path(PyQt6.__file__).resolve().parent / "Qt6" / "plugins" / "platforms"
if plugin_dir.exists():
    os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(plugin_dir))
