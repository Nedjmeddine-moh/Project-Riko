@echo off
echo ========================================
echo  Riko AI - Windows Setup
echo ========================================
echo.

echo Creating virtual environment...
python -m venv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install groq

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo To run Riko AI:
echo   1. Double-click start_riko.bat
echo   OR
echo   2. Run: venv\Scripts\activate.bat
echo      Then: python run.py
echo.
pause
