#!/usr/bin/env powershell
# AgriRover Automated Setup Script
# Run as: powershell -ExecutionPolicy Bypass -File setup.ps1

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "AgriRover Laptop Camera Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if running from correct directory
if (-not (Test-Path ".\models\best.pt")) {
    Write-Host "ERROR: models/best.pt not found!" -ForegroundColor Red
    Write-Host "Make sure you:" -ForegroundColor Yellow
    Write-Host "  1. Are in the agrirover-laptop folder" -ForegroundColor Yellow
    Write-Host "  2. Have copied best.pt to models/best.pt" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/5] Checking Python..." -ForegroundColor Green
$pythonCheck = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK - $pythonCheck" -ForegroundColor Green
} else {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/5] Creating virtual environment..." -ForegroundColor Green
if (-not (Test-Path ".\venv")) {
    python -m venv venv
    Write-Host "OK - Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "OK - Virtual environment already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "[3/5] Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"
Write-Host "OK - Virtual environment activated" -ForegroundColor Green

Write-Host ""
Write-Host "[4/5] Installing dependencies..." -ForegroundColor Green
Write-Host "This may take 2-5 minutes..." -ForegroundColor Yellow

python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to upgrade pip" -ForegroundColor Red
    exit 1
}

python -m pip install --only-binary :all: -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies from requirements.txt" -ForegroundColor Red
    exit 1
}

Write-Host "OK - All dependencies installed" -ForegroundColor Green

Write-Host ""
Write-Host "[5/5] Verifying setup..." -ForegroundColor Green

# Test imports
$testCode = @"
try:
    import flask
    import cv2
    import ultralytics
    import numpy
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
"@

$result = python -c $testCode
$resultText = ($result | Out-String).Trim()
if ($resultText -eq "OK") {
    Write-Host "OK - All packages import successfully" -ForegroundColor Green
} else {
    Write-Host "ERROR: Import test failed - $resultText" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Current Status:" -ForegroundColor Yellow
Write-Host "  - Python: $(python --version)" -ForegroundColor Yellow
Write-Host "  - Virtual Environment: ACTIVATED" -ForegroundColor Yellow
Write-Host "  - Model: models/best.pt (FOUND)" -ForegroundColor Yellow
Write-Host "  - Dependencies: INSTALLED" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Run: python app/app.py" -ForegroundColor Cyan
Write-Host "  2. Open: http://localhost:5000 in browser" -ForegroundColor Cyan
Write-Host "  3. If needed, use dashboard settings to set backend URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop the server: Ctrl+C in the terminal" -ForegroundColor Yellow
Write-Host ""