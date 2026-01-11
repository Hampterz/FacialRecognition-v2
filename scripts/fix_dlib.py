"""
Fix dlib installation - This script will reinstall dlib properly to fix compatibility issues.
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"Running: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def main():
    print("="*60)
    print("DLIB FIX SCRIPT")
    print("="*60)
    print("\nThis will fix the 'Unsupported image type' error by")
    print("reinstalling dlib with a compatible build.")
    print("\nWARNING: This may take several minutes.")
    
    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Step 1: Uninstall current dlib
    print("\n[1/4] Uninstalling current dlib...")
    run_command(f"{sys.executable} -m pip uninstall dlib -y", "Uninstall dlib")
    
    # Step 2: Try installing from conda-forge with specific build
    print("\n[2/4] Installing dlib from conda-forge...")
    success = run_command("conda install -c conda-forge dlib=19.24.2 -y --force-reinstall", "Install dlib from conda-forge")
    
    if not success:
        print("\n[3/4] Conda install failed. Trying pip with pre-built wheel...")
        # Try to find a compatible wheel
        run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrade pip")
        run_command(f"{sys.executable} -m pip install dlib --no-cache-dir", "Install dlib from pip")
    
    # Step 3: Verify installation
    print("\n[4/4] Verifying installation...")
    try:
        import dlib
        import face_recognition
        print(f"✓ dlib version: {dlib.__version__}")
        print("✓ face_recognition imported successfully")
        
        # Test with a simple image
        print("\nTesting face detection...")
        from PIL import Image
        import numpy as np
        
        # Create a test image
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        test_img[25:75, 25:75] = [255, 200, 150]  # Simple square
        
        try:
            # This should work if dlib is properly installed
            locs = face_recognition.face_locations(test_img)
            print("✓ Face detection test passed!")
            print("\n" + "="*60)
            print("SUCCESS! dlib is now properly installed.")
            print("="*60)
            print("\nYou can now run: python app.py")
        except RuntimeError as e:
            if "Unsupported image type" in str(e):
                print("\n⚠ WARNING: dlib still has compatibility issues.")
                print("This may require using Python 3.9 or 3.10 instead of 3.12.")
                print("\nTry creating a new conda environment:")
                print("  conda create -n face_recognition python=3.10")
                print("  conda activate face_recognition")
                print("  conda install -c conda-forge dlib")
                print("  pip install face-recognition opencv-python")
            else:
                print(f"Test error: {e}")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print("\nPlease try installing manually:")
        print("  conda install -c conda-forge dlib")
        print("  pip install face-recognition")

if __name__ == "__main__":
    main()

