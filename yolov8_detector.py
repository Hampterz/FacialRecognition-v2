"""
YOLOv8 Face Detector
Uses YOLOv8 model from Hugging Face for face detection
"""

from huggingface_hub import hf_hub_download
from ultralytics import YOLO
from supervision import Detections
from PIL import Image
import numpy as np
import cv2
from pathlib import Path

class YOLOv8FaceDetector:
    """Face detector using YOLOv8 model."""
    
    def __init__(self):
        self.model = None
        self.model_path = None
        self._load_model()
    
    def _load_model(self):
        """Load YOLOv8 face detection model from Hugging Face."""
        try:
            model_dir = Path("models")
            model_dir.mkdir(exist_ok=True)
            model_path = model_dir / "yolov8_face_detection.pt"
            
            if not model_path.exists():
                print("Downloading YOLOv8 Face Detection model...")
                downloaded_path = hf_hub_download(
                    repo_id="arnabdhar/YOLOv8-Face-Detection",
                    filename="model.pt",
                    local_dir=str(model_dir),
                    local_dir_use_symlinks=False
                )
                downloaded_path_obj = Path(downloaded_path)
                if downloaded_path_obj.exists() and downloaded_path_obj != model_path:
                    downloaded_path_obj.rename(model_path)
                self.model_path = model_path
            else:
                self.model_path = model_path
            
            print(f"Loading YOLOv8 model from {self.model_path}...")
            self.model = YOLO(str(self.model_path))
            print("✓ YOLOv8 model loaded successfully!")
        except Exception as e:
            print(f"Error loading YOLOv8 model: {e}")
            raise
    
    def detect_faces(self, image):
        """Detect faces in an image using YOLOv8."""
        if self.model is None:
            raise RuntimeError("YOLOv8 model not loaded")
        
        if isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        results = self.model(pil_image)
        detections = Detections.from_ultralytics(results[0])
        
        face_locations = []
        for bbox in detections.xyxy:
            x1, y1, x2, y2 = bbox
            top = int(y1)
            right = int(x2)
            bottom = int(y2)
            left = int(x1)
            face_locations.append((top, right, bottom, left))
        
        return face_locations
    
    def detect_faces_cv2(self, frame):
        """Detect faces in OpenCV frame (BGR format)."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.detect_faces(rgb_frame)

