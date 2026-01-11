"""
Verification script to check if everything is set up correctly.
"""

import sys

def check_import(module_name, package_name=None):
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        print(f"✓ {package_name or module_name} - OK")
        return True
    except ImportError as e:
        print(f"✗ {package_name or module_name} - FAILED: {e}")
        return False

def main():
    print("="*60)
    print("Face Recognition System - Setup Verification")
    print("="*60)
    print()
    
    all_ok = True
    
    # Check Python version
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 9):
        print("⚠ WARNING: Python 3.9+ recommended")
    print()
    
    # Check required packages
    print("Checking required packages...")
    print("-" * 60)
    
    checks = [
        ("cv2", "OpenCV"),
        ("face_recognition", "face-recognition"),
        ("numpy", "NumPy"),
        ("PIL", "Pillow"),
        ("tkinter", "Tkinter"),
        ("pickle", "Pickle (built-in)"),
        ("pathlib", "Pathlib (built-in)"),
        ("threading", "Threading (built-in)"),
    ]
    
    for module, name in checks:
        if not check_import(module, name):
            all_ok = False
    
    print()
    print("-" * 60)
    
    # Check directories
    from pathlib import Path
    print("\nChecking directories...")
    print("-" * 60)
    
    dirs = ["training", "validation", "output"]
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✓ {dir_name}/ - exists")
        else:
            print(f"⚠ {dir_name}/ - will be created automatically")
    
    print()
    print("-" * 60)
    
    # Final status
    print()
    if all_ok:
        print("="*60)
        print("✓ ALL CHECKS PASSED!")
        print("="*60)
        print("\nYou can now run the application:")
        print("  python app.py")
        print("  OR")
        print("  Double-click run.bat (Windows)")
        print("="*60)
    else:
        print("="*60)
        print("✗ SOME CHECKS FAILED")
        print("="*60)
        print("\nPlease install missing packages:")
        print("  pip install -r requirements.txt")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()

