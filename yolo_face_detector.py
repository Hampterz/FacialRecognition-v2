"""
YOLOv11 Face Detector - Replaces dlib for face detection
Uses YOLOv11n Face Detection model from Hugging Face
Model: AdamCodd/YOLOv11n-face-detection
Trained on WIDERFACE dataset with excellent accuracy
"""

from huggingface_hub import hf_hub_download
from ultralytics import YOLO
from supervision import Detections
from PIL import Image
import numpy as np
import cv2
from pathlib import Path
import os

class YOLOFaceDetector:
    """Face detector using YOLOv11n model."""
    
    def __init__(self):
        self.model = None
        self.model_path = None
        self._load_model()
    
    def _load_model(self):
        """Load YOLOv11n face detection model from Hugging Face."""
        try:
            # Check if model is already downloaded
            model_dir = Path("models")
            model_dir.mkdir(exist_ok=True)
            model_path = model_dir / "yolov11n_face_detection.pt"
            
            if not model_path.exists():
                print("Downloading YOLOv11n Face Detection model...")
                print("This may take a few minutes on first run...")
                print("Model: AdamCodd/YOLOv11n-face-detection")
                downloaded_path = hf_hub_download(
                    repo_id="AdamCodd/YOLOv11n-face-detection",
                    filename="model.pt",
                    local_dir=str(model_dir),
                    local_dir_use_symlinks=False
                )
                # Rename to our standard name
                downloaded_path_obj = Path(downloaded_path)
                if downloaded_path_obj.exists() and downloaded_path_obj != model_path:
                    downloaded_path_obj.rename(model_path)
                self.model_path = model_path
            else:
                self.model_path = model_path
            
            print(f"Loading YOLOv11n model from {self.model_path}...")
            self.model = YOLO(str(self.model_path))
            print("✓ YOLOv11n model loaded successfully!")
            print("  Model trained on WIDERFACE dataset")
            print("  Easy AP: 94.2%, Medium AP: 92.1%, Hard AP: 81.0%")
        except Exception as e:
            print(f"Error loading YOLOv11n model: {e}")
            raise
    
    def detect_faces(self, image):
        """
        Detect faces in an image using YOLOv11n.
        
        Args:
            image: numpy array (RGB) or PIL Image
            
        Returns:
            List of face locations in format (top, right, bottom, left)
        """
        if self.model is None:
            raise RuntimeError("YOLOv11n model not loaded")
        
        # Convert to PIL Image if numpy array
        if isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        # Run inference
        results = self.model(pil_image)
        detections = Detections.from_ultralytics(results[0])
        
        # Convert to face_recognition format: (top, right, bottom, left)
        face_locations = []
        for bbox in detections.xyxy:
            x1, y1, x2, y2 = bbox
            # Convert from (x1, y1, x2, y2) to (top, right, bottom, left)
            top = int(y1)
            right = int(x2)
            bottom = int(y2)
            left = int(x1)
            face_locations.append((top, right, bottom, left))
        
        return face_locations
    
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

# Global detector instance
_detector_instance = None

def get_detector():
    """Get or create global YOLOv11n detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = YOLOFaceDetector()
    return _detector_instance

