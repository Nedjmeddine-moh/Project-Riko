@echo off
REM run_windows.bat - Launch Riko AI on Windows

echo.
echo ========================================
echo    Starting Riko AI for Windows
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check if GROQ_API_KEY is set
if "%GROQ_API_KEY%"=="" (
    echo ERROR: GROQ_API_KEY environment variable not set!
    echo.
    echo Please set your API key:
    echo 1. Get a free API key from https://console.groq.com/
    echo 2. Set it as environment variable:
    echo    - Press Win+R, type "sysdm.cpl", press Enter
    echo    - Go to "Advanced" tab
    echo    - Click "Environment Variables"
    echo    - Under "User variables", click "New"
    echo    - Variable name: GROQ_API_KEY
    echo    - Variable value: your-api-key-here
    echo.
    echo OR temporarily set it for this session:
    echo    set GROQ_API_KEY=your-api-key-here
    echo.
    pause
    exit /b 1
)

echo Starting Riko AI GUI...
echo.

python gui_windows.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start Riko AI
    echo.
    echo If you see module import errors, run:
    echo    install_windows.bat
    echo.
    pause
)
