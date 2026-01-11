@echo off
echo ========================================
echo Face Recognition System - Dependency Installer
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version
echo.

echo [2/4] Upgrading pip...
python -m pip install --upgrade pip
echo.

echo [3/4] Installing core dependencies (excluding dlib)...
python -m pip install numpy==1.26.4 Pillow==10.3.0 opencv-python==4.11.0.86
python -m pip install ultralytics==8.3.245 huggingface-hub==0.36.0 supervision==0.27.0
python -m pip install torch==2.9.1 torchvision==0.24.1
python -m pip install websockets pyaudio google-genai
python -m pip install retina-face==0.0.17 deepface==0.0.96
echo.

echo [4/4] Installing face-recognition and dlib...
echo NOTE: dlib requires Visual Studio C++ Build Tools on Windows.
echo If this fails, you may need to install Visual Studio Build Tools.
echo.
python -m pip install face-recognition==1.3.0
if errorlevel 1 (
    echo.
    echo ========================================
    echo WARNING: face-recognition installation failed!
    echo This is likely because dlib failed to build.
    echo.
    echo To fix this, you need to install Visual Studio Build Tools:
    echo 1. Download from: https://visualstudio.microsoft.com/downloads/
    echo 2. Install "Desktop development with C++" workload
    echo 3. Then run this script again
    echo.
    echo Alternatively, try installing dlib from conda:
    echo   conda install -c conda-forge dlib
    echo ========================================
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
pause










