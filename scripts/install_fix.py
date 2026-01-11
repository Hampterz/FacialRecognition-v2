"""
Installation fix script for face recognition system.
This script helps resolve common installation issues.
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*60)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def main():
    print("Face Recognition System - Installation Fix Script")
    print("="*60)
    
    # Check Python version
    python_version = sys.version_info
    print(f"\nPython version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major != 3 or python_version.minor < 9:
        print("WARNING: Python 3.9 or 3.10 is recommended!")
        print("Python 3.11+ may have compatibility issues.")
    
    # Upgrade pip
    print("\n1. Upgrading pip...")
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrade pip")
    
    # Install cmake first
    print("\n2. Installing cmake...")
    run_command(f"{sys.executable} -m pip install cmake", "Install cmake")
    
    # Try installing numpy first (often causes issues)
    print("\n3. Installing numpy...")
    if not run_command(f"{sys.executable} -m pip install numpy", "Install numpy"):
        print("\nTrying alternative numpy installation...")
        run_command(f"{sys.executable} -m pip install numpy --upgrade --no-cache-dir", "Install numpy (alternative)")
    
    # Install other packages
    print("\n4. Installing other packages...")
    packages = [
        "Pillow",
        "opencv-python"
    ]
    
    for package in packages:
        run_command(f"{sys.executable} -m pip install {package}", f"Install {package}")
    
    # Try installing dlib
    print("\n5. Installing dlib (this may take a while)...")
    if not run_command(f"{sys.executable} -m pip install dlib", "Install dlib"):
        print("\nWARNING: dlib installation failed!")
        print("You may need to:")
        print("  - Install Visual Studio Build Tools (Windows)")
        print("  - Install CMake and add to PATH")
        print("  - Or use conda: conda install -c conda-forge dlib")
    
    # Install face-recognition
    print("\n6. Installing face-recognition...")
    run_command(f"{sys.executable} -m pip install face-recognition", "Install face-recognition")
    
    print("\n" + "="*60)
    print("Installation complete!")
    print("Try running: python app.py")
    print("="*60)

if __name__ == "__main__":
    main()

