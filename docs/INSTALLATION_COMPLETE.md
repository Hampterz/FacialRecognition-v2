# Quick Installation Guide

## For Windows Users

1. **Double-click `scripts/INSTALL.bat`**
   - This will install all dependencies automatically
   - Takes 10-15 minutes
   - Follow any prompts that appear

2. **Run the application**
   - Double-click `scripts/run.bat`, OR
   - Run: `python app.py`

## For Linux/macOS Users

1. **Make the script executable** (first time only):
   ```bash
   chmod +x scripts/INSTALL.sh
   ```

2. **Run the installation script**:
   ```bash
   ./scripts/INSTALL.sh
   ```

3. **Run the application**:
   ```bash
   python3 app.py
   ```

## What Gets Installed

The installation script automatically installs:
- ✅ All Python packages from `requirements.txt`
- ✅ OpenCV, NumPy, Pillow (image processing)
- ✅ PyTorch (deep learning framework)
- ✅ YOLO models (face detection)
- ✅ face_recognition library (face encoding)
- ✅ Google Sheets integration (gspread, oauth2client)
- ✅ All other dependencies

## Troubleshooting

### face-recognition Installation Fails (Windows)

**Problem:** `face-recognition` requires `dlib`, which needs Visual Studio C++ Build Tools.

**Solution:**
1. Download Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/
2. Install "Desktop development with C++" workload
3. Run `INSTALL.bat` again

**Alternative (Easier):**
1. Install Anaconda/Miniconda: https://www.anaconda.com/download
2. Run: `conda install -c conda-forge dlib`
3. Run: `pip install face-recognition`
4. Run `INSTALL.bat` again

### face-recognition Installation Fails (Linux)

**Problem:** Missing system dependencies for building dlib.

**Solution (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev
```

Then run `INSTALL.sh` again.

**Solution (macOS):**
```bash
brew install cmake dlib
```

Then run `INSTALL.sh` again.

### Other Issues

- **Python not found**: Install Python 3.9+ from https://www.python.org/downloads/
- **pip not found**: Upgrade pip: `python -m ensurepip --upgrade`
- **Network errors**: Check your internet connection, some packages are large (PyTorch is ~2GB)

## Optional: Google Sheets Setup (for Smart Attendance)

See `SETUP_CREDENTIALS.md` for detailed instructions on setting up Google Sheets integration.

## After Installation

1. **Train the model** with photos of people you want to recognize
2. **Use Live Recognition** to test recognition
3. **Set up Smart Attendance** (optional) for automated attendance tracking

That's it! The system is ready to use. 🎉
