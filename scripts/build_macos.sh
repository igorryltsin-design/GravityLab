#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYQT_PLUGIN_DIR="$(python3 - <<'PY'
from pathlib import Path
import PyQt6
print(Path(PyQt6.__file__).resolve().parent / 'Qt6' / 'plugins')
PY
)"
APP_BUNDLE="$ROOT_DIR/dist/GravityLab.app"
APP_PLUGIN_DIR="$APP_BUNDLE/Contents/Frameworks/PyQt6/Qt6/plugins"

cd "$ROOT_DIR"

python3 -m pip install --upgrade pip
python3 -m pip install pyinstaller
python3 -m pip install -e .

python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name GravityLab \
  --paths "$ROOT_DIR/src" \
  "$ROOT_DIR/gravity_sim_study_pyqt.py"

# Conda-based PyQt6 can expose a global Qt5 plugins directory; PyInstaller may
# collect those incompatible plugins into the bundle. Replace them with the
# actual Qt6 plugins shipped with the installed PyQt6 package.
rm -rf "$APP_PLUGIN_DIR"
cp -R "$PYQT_PLUGIN_DIR" "$APP_PLUGIN_DIR"
codesign --force --deep --sign - "$APP_BUNDLE"

echo
echo "Сборка завершена: $APP_BUNDLE"
