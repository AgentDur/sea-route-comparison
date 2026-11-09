@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo     Sea route comparison - Python
 echo ========================================
where py >nul 2>nul
if errorlevel 1 (
    echo Python 3 is not found. Install Python from python.org and enable PATH.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 (echo Failed to create virtual environment. & pause & exit /b 1)
)
.venv\Scripts\python.exe -c "import geographiclib, matplotlib" >nul 2>nul
if errorlevel 1 (
    echo Installing Python packages; internet is required for the first run...
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (echo Install failed. & pause & exit /b 1)
)
.venv\Scripts\python.exe route_calc.py %*
pause
