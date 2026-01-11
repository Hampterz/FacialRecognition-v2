"""
RetinaFace Face Detector
Uses RetinaFace library for face detection with facial landmarks
Source: https://github.com/serengil/retinaface
"""

# Don't import at module level - import lazily to avoid errors
RetinaFace = None
from PIL import Image
import numpy as np
import cv2
from pathlib import Path

class RetinaFaceDetector:
    """Face detector using RetinaFace model."""
    
    def __init__(self):
        global RetinaFace
        # Lazy import to avoid errors if not installed or has dependency issues
        if RetinaFace is None:
            try:
                from retinaface import RetinaFace as RF
                RetinaFace = RF
            except ImportError as e:
                raise ImportError(
                    f"retina-face package not installed. Install with: pip install retina-face\n"
                    f"Original error: {str(e)}"
                )
            except ValueError as e:
                # Handle tf-keras dependency issue
                error_msg = str(e)
                if "tf-keras" in error_msg.lower():
                    raise ImportError(
                        "RetinaFace requires tf-keras package.\n\n"
                        "Please install it:\n"
                        "pip install tf-keras\n\n"
                        "Or use YOLOv8 or YOLOv11 instead."
                    )
                raise
        
        self.model_loaded = True  # RetinaFace loads automatically on import
        print("RetinaFace model loaded successfully!")
        print("  RetinaFace: Deep learning based face detector with landmarks")
    
    def detect_faces(self, image):
        """
        Detect faces in an image using RetinaFace.
        
        Args:
            image: numpy array (RGB) or PIL Image
            
        Returns:
            List of face locations in format (top, right, bottom, left)
        """
        # Convert to numpy array if PIL Image
        if isinstance(image, Image.Image):
            image_array = np.array(image)
        elif isinstance(image, np.ndarray):
            image_array = image
        else:
            raise ValueError("Image must be PIL Image or numpy array")
        
        # Save temporarily if it's an array (RetinaFace needs file path)
        # Or convert to RGB if needed
        if len(image_array.shape) == 3:
            # Ensure RGB
            if image_array.shape[2] == 4:  # RGBA
                image_array = image_array[:, :, :3]
        
        # RetinaFace can work with numpy arrays directly in newer versions
        # But for compatibility, we'll save to temp file
        import tempfile
        import os
        
        temp_file = None
        try:
            # Create temporary file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg')
            os.close(temp_fd)
            
            # Save image to temp file
            temp_image = Image.fromarray(image_array)
            temp_image.save(temp_path, 'JPEG')
            
            # Detect faces
            faces = RetinaFace.detect_faces(temp_path)
            
            # Convert to face_recognition format: (top, right, bottom, left)
            face_locations = []
            for face_key, face_data in faces.items():
                facial_area = face_data['facial_area']
                # RetinaFace returns [x1, y1, x2, y2]
                x1, y1, x2, y2 = facial_area
                # Convert to (top, right, bottom, left)
                top = int(y1)
                right = int(x2)
                bottom = int(y2)
                left = int(x1)
                face_locations.append((top, right, bottom, left))
            
            return face_locations
            
        except Exception as e:
            print(f"Error in RetinaFace detection: {e}")
            return []
        finally:
            # Clean up temp file
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
    
    def detect_faces_cv2(self, frame):
        """
        Detect faces in OpenCV frame (BGR format).
        
        Args:
            frame: OpenCV frame (BGR)
            
        Returns:
            List of face locations in format (top, right, bottom, left)
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.detect_faces(rgb_frame)

