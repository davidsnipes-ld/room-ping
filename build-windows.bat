@echo off
cd /d "%~dp0"
echo Building RoomPing Pro for Windows...
echo.
echo Installing dependencies (user install - no admin required)...
python -m pip install --user --quiet pyinstaller -r requirements.txt
if errorlevel 1 (
    echo Try: py -3 -m pip install --user pyinstaller -r requirements.txt
    pause
    exit /b 1
)
echo.
echo Running PyInstaller...
python -m PyInstaller --noconfirm RoomPingPro.spec
if errorlevel 1 (
    py -3 -m PyInstaller --noconfirm RoomPingPro.spec
)
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)
echo.
echo Done. Application: dist\RoomPingPro.exe
echo.
pause
