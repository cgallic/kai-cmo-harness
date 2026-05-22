@echo off
echo ===================================================
echo   Kai Marketing OS - One-Click Dashboard Deployer
echo ===================================================
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.x and ensure it is added to your environment variables.
    pause
    exit /b 1
)
python scripts\deploy.py
pause
