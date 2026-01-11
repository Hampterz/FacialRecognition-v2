# Dlib Compatibility Issue - Known Problem

## Issue
If you're getting "Unsupported image type, must be 8bit gray or RGB image" errors, this is a known compatibility issue with the conda dlib build.

## Solutions

### Solution 1: Use Pre-built dlib Wheel (Recommended)
```bash
# Uninstall conda dlib
conda uninstall dlib -y

# Install pre-built wheel (if available for your Python version)
pip install dlib-binary
# OR try:
pip install https://github.com/sachadee/Dlib/releases/download/v19.22/dlib-19.22.99-cp312-cp312-win_amd64.whl
```

### Solution 2: Use Different Python Version
The conda dlib works better with Python 3.9 or 3.10:
```bash
conda create -n face_recognition python=3.10
conda activate face_recognition
conda install -c conda-forge dlib
pip install face-recognition opencv-python
```

### Solution 3: Build dlib from Source
Requires Visual Studio Build Tools:
```bash
pip install cmake
pip install dlib --no-binary dlib
```

### Solution 4: Use Alternative (Temporary Workaround)
The app will automatically try to work around this issue, but if it persists, you may need to reinstall dlib using one of the methods above.

