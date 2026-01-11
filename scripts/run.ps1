Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Face Recognition System - Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[1/3] Checking Python installation..." -ForegroundColor Yellow
    Write-Host $pythonVersion
    Write-Host ""
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from https://www.python.org/downloads/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if dependencies are installed
Write-Host "[2/3] Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import cv2" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "cv2 not found"
    }
    Write-Host "Dependencies are installed." -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "Dependencies not found. Installing from requirements.txt..." -ForegroundColor Yellow
    Write-Host "This may take several minutes..." -ForegroundColor Yellow
    Write-Host ""
    
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: Failed to install dependencies!" -ForegroundColor Red
        Write-Host "Please check the error messages above." -ForegroundColor Red
        Write-Host ""
        Write-Host "You can try installing manually:" -ForegroundColor Yellow
        Write-Host "  pip install -r requirements.txt" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Host ""
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
    Write-Host ""
}

# Start the application
Write-Host "[3/3] Starting application..." -ForegroundColor Yellow
Write-Host ""
python app.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Application failed to start!" -ForegroundColor Red
    Write-Host "Check the error messages above." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

