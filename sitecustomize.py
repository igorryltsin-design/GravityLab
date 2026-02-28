import os
from pathlib import Path

os.environ.setdefault("QT_API", "pyqt6")

try:
    import PyQt6
except Exception:
    PyQt6 = None

if PyQt6 is not None:
    plugin_dir = Path(PyQt6.__file__).resolve().parent / "Qt6" / "plugins" / "platforms"
    if plugin_dir.exists():
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(plugin_dir))
