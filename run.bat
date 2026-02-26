@echo off
cd /d "%~dp0"
echo RoomPing Pro - checking dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo Try: py -3 -m pip install -r requirements.txt
    pause
    exit /b 1
)
echo Starting...
python main.py
if errorlevel 1 (
    py -3 main.py
)
pause
