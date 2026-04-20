@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo  MemTime Timesheeter - Setup
echo ==========================================
echo.

REM Check Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not on PATH.
    echo.
    echo Please install Python from https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Installing dependencies...
echo.
pip install tzlocal requests
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.

REM Create env.py if it doesn't already exist
if exist "%~dp0env.py" (
    echo env.py already exists - skipping credential setup.
) else (
    echo Setting up LiquidPlanner credentials...
    echo Enter the email and password you use to log into LiquidPlanner Classic.
    echo.
    python -c "email=input('LiquidPlanner email: '); pwd=input('LiquidPlanner password: '); content='LIQUID_PLANNER_EMAIL = ' + repr(email) + '\nLIQUID_PLANNER_PASSWORD = ' + repr(pwd) + '\n'; open('env.py','w').write(content); print('\nenv.py created successfully.')"
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Failed to create env.py.
        pause
        exit /b 1
    )
)

echo.
echo ==========================================
echo  Setup complete! You can now run the
echo  Timesheet, RefreshTasks and ArchiveTasks
echo  batch files.
echo ==========================================
echo.
pause
