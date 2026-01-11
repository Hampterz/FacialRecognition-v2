"""
Script to convert training images to a format compatible with dlib.
Run this if you're getting "Unsupported image type" errors.
"""

from pathlib import Path
from PIL import Image
import shutil

def fix_images_in_directory(directory):
    """Convert all images in directory to RGB JPEG format."""
    directory = Path(directory)
    fixed_count = 0
    error_count = 0
    
    for img_path in directory.rglob("*"):
        if img_path.is_file() and img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            try:
                # Open and convert image
                img = Image.open(img_path)
                
                # Convert to RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as new JPEG (this ensures proper format)
                new_path = img_path.with_suffix('.jpg')
                if new_path != img_path:
                    img.save(new_path, 'JPEG', quality=95)
                    img_path.unlink()  # Delete old file
                    print(f"Converted: {img_path.name} -> {new_path.name}")
                else:
                    # Same file, just resave to fix format
                    img.save(img_path, 'JPEG', quality=95)
                    print(f"Fixed: {img_path.name}")
                
                fixed_count += 1
            except Exception as e:
                print(f"Error processing {img_path.name}: {e}")
                error_count += 1
    
    print(f"\n✓ Fixed {fixed_count} image(s)")
    if error_count > 0:
        print(f"⚠ {error_count} image(s) had errors")

if __name__ == "__main__":
    print("Fixing training images...")
    fix_images_in_directory("training")
    print("\nDone! Try training again.")

