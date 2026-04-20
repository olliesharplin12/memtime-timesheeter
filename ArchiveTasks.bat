@echo off
cd /d "%~dp0"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not on PATH.
    echo Please run Setup.bat first.
    pause
    exit /b 1
)

if not exist "%~dp0env.py" (
    echo ERROR: env.py not found. Please run Setup.bat first.
    pause
    exit /b 1
)

python ArchiveMemtimeTasks.py
