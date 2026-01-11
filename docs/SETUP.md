# Setup Guide

## Quick Installation

### Step 1: Install Prerequisites

**Windows:**
1. Install CMake from https://cmake.org/download/
2. Install Visual Studio Build Tools (for C++ compiler):
   - Download from: https://visualstudio.microsoft.com/downloads/
   - Select "Desktop development with C++" workload
   - OR install MinGW: `choco install mingw`

**Alternative for Windows (Easier):**
- Install pre-built wheels if available
- Use conda: `conda install -c conda-forge dlib face-recognition`

### Step 2: Install Python Packages

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install packages
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: If Installation Fails

**If dlib installation fails:**
```bash
# Try installing dlib separately first
pip install cmake
pip install dlib

# Then install the rest
pip install face-recognition opencv-python pillow numpy
```

**If numpy installation fails:**
- Make sure you're using Python 3.9 or 3.10 (3.11+ may have issues)
- Try: `pip install numpy --upgrade`
- Or use conda: `conda install numpy`

### Step 4: Run the Application

```bash
python app.py
```

## Troubleshooting

**"CMake not found" error:**
- Install CMake and add it to your PATH
- Or use: `pip install cmake`

**"Microsoft Visual C++ 14.0 or greater is required" (Windows):**
- Install Visual Studio Build Tools
- Or use conda instead of pip

**Camera not working:**
- Check camera permissions in Windows Settings
- Try different camera index in Settings (0, 1, 2, etc.)
- Make sure no other app is using the camera

**Import errors:**
- Make sure virtual environment is activated
- Reinstall packages: `pip install -r requirements.txt --force-reinstall`

