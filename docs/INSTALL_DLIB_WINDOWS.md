# Installing dlib on Windows

The `face-recognition` library requires `dlib`, which needs to be compiled on Windows. This requires Visual Studio C++ Build Tools.

## Option 1: Install Visual Studio Build Tools (Recommended)

1. Download Visual Studio Build Tools from:
   https://visualstudio.microsoft.com/downloads/
   
2. Run the installer and select:
   - **"Desktop development with C++"** workload
   - This includes the C++ compiler needed to build dlib

3. After installation, restart your computer

4. Then install face-recognition:
   ```bash
   pip install face-recognition==1.3.0
   ```

## Option 2: Use Conda (Easier - Pre-built wheels)

If you have Anaconda or Miniconda installed:

```bash
conda install -c conda-forge dlib
pip install face-recognition==1.3.0
```

## Option 3: Use Pre-built Wheel (If available)

Some users have success with pre-built wheels. Try:

```bash
pip install dlib-bin
pip install face-recognition==1.3.0
```

If that doesn't work, you'll need Option 1 or 2.

## Verify Installation

After installing, verify it works:

```bash
python -c "import face_recognition; print('Success!')"
```

## Troubleshooting

- **"CMake not found"**: Install CMake from https://cmake.org/download/
- **"Visual C++ not found"**: Install Visual Studio Build Tools (Option 1)
- **Still failing?**: Try using conda (Option 2) - it has pre-built wheels










