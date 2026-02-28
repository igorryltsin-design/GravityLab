@echo off
setlocal

set ROOT_DIR=%~dp0..
cd /d "%ROOT_DIR%"

py -m pip install --upgrade pip
if errorlevel 1 exit /b %errorlevel%

py -m pip install pyinstaller
if errorlevel 1 exit /b %errorlevel%

py -m pip install -e .
if errorlevel 1 exit /b %errorlevel%

py -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name GravityLab ^
  --paths src ^
  gravity_sim_study_pyqt.py
if errorlevel 1 exit /b %errorlevel%

echo.
echo Сборка завершена: %ROOT_DIR%\dist\GravityLab\GravityLab.exe
