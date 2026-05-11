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

# В окружениях Conda рядом с PyQt6 может быть глобальная папка Qt5 plugins.
# PyInstaller иногда случайно подхватывает эти несовместимые плагины в бандл.
# Поэтому явно заменяем плагины в .app на те, что реально поставляются с Qt6.
rm -rf "$APP_PLUGIN_DIR"
cp -R "$PYQT_PLUGIN_DIR" "$APP_PLUGIN_DIR"
codesign --force --deep --sign - "$APP_BUNDLE"

echo
echo "Сборка завершена: $APP_BUNDLE"
