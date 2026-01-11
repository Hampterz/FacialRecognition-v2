#!/bin/bash
# ========================================
# Facial Recognition System - Complete Installation
# This script installs all dependencies automatically
# For Linux and macOS
# ========================================

echo ""
echo "========================================"
echo "Facial Recognition System"
echo "Complete Installation Script"
echo "========================================"
echo ""
echo "This script will:"
echo "  1. Check Python installation"
echo "  2. Upgrade pip to latest version"
echo "  3. Install all required dependencies"
echo "  4. Verify installation"
echo ""
echo "Please wait, this may take 10-15 minutes..."
echo ""
read -p "Press Enter to continue..."

# ========================================
# Step 1: Check Python Installation
# ========================================
echo ""
echo "[Step 1/4] Checking Python installation..."
echo ""

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH!"
    echo ""
    echo "Please install Python 3.9 or later:"
    echo "  Linux (Ubuntu/Debian): sudo apt-get install python3 python3-pip python3-venv"
    echo "  Linux (Fedora): sudo dnf install python3 python3-pip"
    echo "  macOS: brew install python@3.12"
    echo ""
    exit 1
fi

python3 --version
echo "Python found! ✓"
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo "ERROR: pip is not installed!"
    echo ""
    echo "Please install pip:"
    echo "  Linux (Ubuntu/Debian): sudo apt-get install python3-pip"
    echo "  macOS: python3 -m ensurepip --upgrade"
    echo ""
    exit 1
fi

# ========================================
# Step 2: Upgrade pip
# ========================================
echo "[Step 2/4] Upgrading pip to latest version..."
echo ""

python3 -m pip install --upgrade pip
if [ $? -ne 0 ]; then
    echo "WARNING: Failed to upgrade pip, continuing anyway..."
    echo ""
else
    echo "pip upgraded successfully! ✓"
    echo ""
fi

# ========================================
# Step 3: Install Dependencies from requirements.txt
# ========================================
echo "[Step 3/4] Installing all dependencies from requirements.txt..."
echo "This will take several minutes. Please be patient..."
echo ""

python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo "WARNING: Some dependencies failed to install!"
    echo "========================================"
    echo ""
    echo "This might be because:"
    echo "  1. System dependencies are missing (CMake, g++, etc.)"
    echo "  2. Some packages may have network issues"
    echo ""
    echo "For face-recognition (requires dlib), you may need:"
    echo "  Linux (Ubuntu/Debian):"
    echo "    sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev"
    echo "  macOS:"
    echo "    brew install cmake dlib"
    echo ""
    echo "Then run this script again."
    echo ""
    echo "========================================"
    echo ""
    read -p "Press Enter to continue..."
    exit 1
fi

echo ""
echo "All dependencies installed successfully! ✓"
echo ""

# ========================================
# Step 4: Verify Critical Packages
# ========================================
echo "[Step 4/4] Verifying critical packages..."
echo ""

python3 -c "import cv2; print('OpenCV: OK')" 2>/dev/null || echo "OpenCV: FAILED"
python3 -c "import numpy; print('NumPy: OK')" 2>/dev/null || echo "NumPy: FAILED"
python3 -c "import PIL; print('Pillow: OK')" 2>/dev/null || echo "Pillow: FAILED"
python3 -c "import torch; print('PyTorch: OK')" 2>/dev/null || echo "PyTorch: FAILED"
python3 -c "import face_recognition; print('face_recognition: OK')" 2>/dev/null || echo "face_recognition: FAILED (may need system dependencies)"
python3 -c "import gspread; print('gspread: OK')" 2>/dev/null || echo "gspread: FAILED"
python3 -c "import oauth2client; print('oauth2client: OK')" 2>/dev/null || echo "oauth2client: FAILED"
python3 -c "from ultralytics import YOLO; print('Ultralytics: OK')" 2>/dev/null || echo "Ultralytics: FAILED"

echo ""

# ========================================
# Installation Complete
# ========================================
echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Configure Google Sheets (optional - for Smart Attendance):"
echo "     - See SETUP_CREDENTIALS.md for instructions"
echo "     - Update attendance_sheet.py with your credentials"
echo ""
echo "  2. Run the application:"
echo "     - Run: python3 app.py"
echo ""
echo "  3. Train the model:"
echo "     - Click 'Train Model' in the application"
echo "     - Add photos of people you want to recognize"
echo ""
echo "========================================"
echo ""
