@echo off
chcp 65001 >nul
title AI Desktop Virtual Voice Assistant
echo ======================================================
echo          AI Desktop Virtual Voice Assistant
echo     Multimodal Voice Automation & Desktop Control
echo ======================================================
echo.

:: Fast dependency check
python -c "import streamlit, pyttsx3, speech_recognition, psutil" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [Checking dependencies - first run only...]
    python -m pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install dependencies. Please check your Python environment.
        pause
        exit /b 1
    )
)

echo [Launching application in dedicated window...]
echo ======================================================
echo  * Opening in its own separate window.
echo  * Your other browser tabs will NOT be affected.
echo  * Click 'Stop Session' in the app to close cleanly.
echo ======================================================
echo.

python launch.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with error code %ERRORLEVEL%.
    pause
)
