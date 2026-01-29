@echo off
REM install_windows.bat - Install Riko AI dependencies on Windows

echo.
echo ========================================
echo   Riko AI - Windows Installation
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo Installing required packages...
echo.

REM Install core dependencies
echo [1/4] Installing Groq API...
pip install groq

echo.
echo [2/4] Installing Text-to-Speech (pyttsx3)...
pip install pyttsx3

echo.
echo [3/4] Installing Speech Recognition...
pip install SpeechRecognition

echo.
echo [4/4] Installing PyAudio (for microphone input)...
echo Note: This may require Visual C++ Build Tools on Windows
pip install pyaudio

if errorlevel 1 (
    echo.
    echo WARNING: PyAudio installation failed!
    echo.
    echo This is common on Windows. Try one of these solutions:
    echo.
    echo Solution 1: Install pre-compiled wheel
    echo    Download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
    echo    Then: pip install downloaded-file.whl
    echo.
    echo Solution 2: Install via pipwin
    echo    pip install pipwin
    echo    pipwin install pyaudio
    echo.
    echo You can still use Riko without voice input!
    echo Text-to-Speech will still work.
    echo.
)

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Set your GROQ_API_KEY environment variable
echo 2. Run: run_windows.bat
echo.
echo Voice features:
echo - Text-to-Speech: Should work out of the box
echo - Speech-to-Text: Requires PyAudio (see warnings above)
echo.
pause
