@echo off
REM AgriRover Automated Setup Script (Batch)
REM Run as: setup.bat

color 0B
title AgriRover Laptop Camera Setup

echo.
echo =====================================
echo AgriRover Laptop Camera Setup
echo =====================================
echo.

REM Check if model exists
if not exist "models\best.pt" (
    echo ERROR: models\best.pt not found!
    echo.
    echo Make sure you:
    echo   1. Are in the agrirover-laptop folder
    echo   2. Have copied best.pt to models\best.pt
    echo.
    pause
    exit /b 1
)

REM Check Python
echo [1/5] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)
python --version
echo OK
echo.

REM Create venv
echo [2/5] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo OK - Virtual environment created
) else (
    echo OK - Virtual environment already exists
)
echo.

REM Activate venv
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
echo OK - Virtual environment activated
echo.

REM Install dependencies
echo [4/5] Installing dependencies...
echo This may take 2-5 minutes...
echo.
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ERROR: Failed to upgrade pip
    pause
    exit /b 1
)

python -m pip install --only-binary :all: -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies from requirements.txt
    pause
    exit /b 1
)

echo OK - All dependencies installed
echo.

REM Verify
echo [5/5] Verifying setup...
python -c "import flask; import cv2; import ultralytics; import numpy; print('OK')" >nul 2>&1
if %errorlevel% equ 0 (
    echo OK - All packages import successfully
) else (
    echo ERROR: Import test failed
    pause
    exit /b 1
)
echo.

REM Success
echo =====================================
echo Setup Complete!
echo =====================================
echo.
echo Current Status:
python --version
echo Virtual Environment: ACTIVATED
echo Model: models\best.pt (FOUND)
echo Dependencies: INSTALLED
echo.
echo Next Steps:
echo   1. Run: python app\app.py
echo   2. Open: http://localhost:5000 in browser
echo   3. If needed, click Settings - enter http://localhost:5000
echo.
echo To stop the server: Press Ctrl+C in the terminal
echo.
pause