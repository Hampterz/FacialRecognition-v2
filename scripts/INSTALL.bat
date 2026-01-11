@echo off
REM ========================================
REM Facial Recognition System - Complete Installation
REM This script installs all dependencies automatically
REM ========================================

echo.
echo ========================================
echo Facial Recognition System
echo Complete Installation Script
echo ========================================
echo.
echo This script will:
echo   1. Check Python installation
echo   2. Upgrade pip to latest version
echo   3. Install all required dependencies
echo   4. Verify installation
echo.
echo Please wait, this may take 10-15 minutes...
echo.
pause

REM ========================================
REM Step 1: Check Python Installation
REM ========================================
echo.
echo [Step 1/4] Checking Python installation...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.9 or later from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

python --version
echo Python found! ✓
echo.

REM ========================================
REM Step 2: Upgrade pip
REM ========================================
echo [Step 2/4] Upgrading pip to latest version...
echo.

python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: Failed to upgrade pip, continuing anyway...
    echo.
) else (
    echo pip upgraded successfully! ✓
    echo.
)

REM ========================================
REM Step 3: Install Dependencies from requirements.txt
REM ========================================
echo [Step 3/4] Installing all dependencies from requirements.txt...
echo This will take several minutes. Please be patient...
echo.

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ========================================
    echo WARNING: Some dependencies failed to install!
    echo ========================================
    echo.
    echo This might be because:
    echo   1. face-recognition requires dlib, which needs Visual Studio C++ Build Tools
    echo   2. Some packages may have network issues
    echo.
    echo If face-recognition failed, you have two options:
    echo.
    echo Option A - Install Visual Studio Build Tools (Recommended):
    echo   1. Download from: https://visualstudio.microsoft.com/downloads/
    echo   2. Install "Visual Studio Build Tools"
    echo   3. Select "Desktop development with C++" workload
    echo   4. Run this script again
    echo.
    echo Option B - Use Conda (Easier for dlib):
    echo   1. Install Anaconda/Miniconda from: https://www.anaconda.com/download
    echo   2. Run: conda install -c conda-forge dlib
    echo   3. Run: pip install face-recognition
    echo   4. Run this script again
    echo.
    echo ========================================
    echo.
    pause
    exit /b 1
)

echo.
echo All dependencies installed successfully! ✓
echo.

REM ========================================
REM Step 4: Verify Critical Packages
REM ========================================
echo [Step 4/4] Verifying critical packages...
echo.

python -c "import cv2; print('OpenCV: OK')" 2>nul || echo OpenCV: FAILED
python -c "import numpy; print('NumPy: OK')" 2>nul || echo NumPy: FAILED
python -c "import PIL; print('Pillow: OK')" 2>nul || echo Pillow: FAILED
python -c "import torch; print('PyTorch: OK')" 2>nul || echo PyTorch: FAILED
python -c "import face_recognition; print('face_recognition: OK')" 2>nul || echo face_recognition: FAILED (requires dlib)
python -c "import gspread; print('gspread: OK')" 2>nul || echo gspread: FAILED
python -c "import oauth2client; print('oauth2client: OK')" 2>nul || echo oauth2client: FAILED
python -c "from ultralytics import YOLO; print('Ultralytics: OK')" 2>nul || echo Ultralytics: FAILED

echo.

REM ========================================
REM Installation Complete
REM ========================================
echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Configure Google Sheets (optional - for Smart Attendance):
echo      - See SETUP_CREDENTIALS.md for instructions
echo      - Update attendance_sheet.py with your credentials
echo.
echo   2. Run the application:
echo      - Double-click run.bat, OR
echo      - Run: python app.py
echo.
echo   3. Train the model:
echo      - Click "Train Model" in the application
echo      - Add photos of people you want to recognize
echo.
echo ========================================
echo.
pause
