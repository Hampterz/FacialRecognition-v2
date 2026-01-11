"""
DeepFace detector for face detection and recognition with emotion, age, race, and gender analysis.
Based on: https://github.com/serengil/deepface
"""

import numpy as np
from pathlib import Path
import cv2
from PIL import Image

# Lazy import to prevent startup crashes
DeepFace = None
retinaface_available = False

def _import_deepface():
    """Lazy import of DeepFace."""
    global DeepFace, retinaface_available
    if DeepFace is None:
        try:
            from deepface import DeepFace as DF
            DeepFace = DF
            retinaface_available = True
            print("✓ DeepFace imported successfully!")
        except ImportError as e:
            raise ImportError(
                f"deepface package not installed. Install with: pip install deepface\n"
                f"Original error: {str(e)}"
            )
    return DeepFace


class DeepFaceDetector:
    """Face detector and analyzer using DeepFace library."""
    
    def __init__(self):
        """Initialize DeepFace detector."""
        _import_deepface()
        self.model_loaded = True
        print("✓ DeepFace detector initialized!")
    
    def detect_faces(self, image):
        """
        Detect faces in an image.
        
        Args:
            image: RGB numpy array (H, W, 3)
            
        Returns:
            List of face locations in format (top, right, bottom, left)
        """
        try:
            # DeepFace can use multiple backends - try RetinaFace first, then OpenCV
            import tempfile
            import os
            
            temp_path = None
            try:
                # Create temporary file
                temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg')
                os.close(temp_fd)
                
                # Save image to temp file
                temp_image = Image.fromarray(image)
                temp_image.save(temp_path, 'JPEG')
                
                # Try to get face locations using RetinaFace detector (if available)
                try:
                    from retinaface import RetinaFace
                    detections = RetinaFace.detect_faces(temp_path)
                    
                    face_locations = []
                    for face_key, face_data in detections.items():
                        facial_area = face_data['facial_area']
                        x1, y1, x2, y2 = facial_area
                        top = int(y1)
                        right = int(x2)
                        bottom = int(y2)
                        left = int(x1)
                        face_locations.append((top, right, bottom, left))
                    
                    if face_locations:
                        return face_locations
                except:
                    pass  # RetinaFace not available, fall through to OpenCV
                
                # Fallback to OpenCV for detection
                return self._detect_with_opencv(image)
                
            finally:
                # Clean up temp file
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error in DeepFace detection: {e}")
            # Fallback to OpenCV
            return self._detect_with_opencv(image)
    
    def _detect_with_opencv(self, image):
        """Fallback face detection using OpenCV."""
        try:
            import cv2
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            face_locations = []
            for (x, y, w, h) in faces:
                top = int(y)
                right = int(x + w)
                bottom = int(y + h)
                left = int(x)
                face_locations.append((top, right, bottom, left))
            
            return face_locations
        except Exception as e:
            print(f"Error in OpenCV fallback detection: {e}")
            return []
    
    def analyze_face(self, image_path, actions=None):
        """
        Analyze face for emotion, age, gender, and race.
        Handles partial failures gracefully - if one action fails, others still work.
        
        Args:
            image_path: Path to image file or numpy array
            actions: List of actions ['emotion', 'age', 'gender', 'race'] or None for all
            
        Returns:
            Dictionary with analysis results (may be partial if some actions fail)
        """
        if actions is None:
            actions = ['emotion', 'age', 'gender', 'race']
        
        result = {}
        
        # Try each action separately so failures don't break everything
        for action in actions:
            try:
                action_result = DeepFace.analyze(
                    img_path=image_path,
                    actions=[action],  # Analyze one at a time
                    enforce_detection=False,
                    detector_backend='retinaface',
                    silent=True  # Suppress progress bars
                )
                
                # Handle both single dict and list of dicts
                if isinstance(action_result, list):
                    action_result = action_result[0]
                
                # Merge results
                if action_result:
                    result.update(action_result)
            except Exception as e:
                # Log error but continue with other actions
                print(f"Warning: DeepFace {action} analysis failed: {str(e)[:100]}")
                # Set default values for failed actions
                if action == 'emotion':
                    result['dominant_emotion'] = 'N/A'
                elif action == 'age':
                    result['age'] = 0
                elif action == 'gender':
                    result['dominant_gender'] = 'N/A'
                elif action == 'race':
                    result['dominant_race'] = 'N/A'
        
        return result
    
    def verify_faces(self, img1_path, img2_path, model_name='VGG-Face'):
        """
        Verify if two faces belong to the same person.
        
        Args:
            img1_path: Path to first image
            img2_path: Path to second image
            model_name: Model to use ('VGG-Face', 'Facenet', 'OpenFace', etc.)
            
        Returns:
            Dictionary with 'verified' (bool) and 'distance' (float)
        """
        try:
            result = DeepFace.verify(
                img1_path=img1_path,
                img2_path=img2_path,
                model_name=model_name,
                enforce_detection=False,
                detector_backend='retinaface'
            )
            return result
        except Exception as e:
            print(f"Error in DeepFace verification: {e}")
            return {'verified': False, 'distance': 1.0}
    
    def represent_face(self, image_path, model_name='VGG-Face'):
        """
        Get face embedding/representation.
        
        Args:
            image_path: Path to image file
            model_name: Model to use for embedding
            
        Returns:
            Face embedding vector
        """
        try:
            result = DeepFace.represent(
                img_path=image_path,
                model_name=model_name,
                enforce_detection=False,
                detector_backend='retinaface'
            )
            # Return first face embedding
            if isinstance(result, list) and len(result) > 0:
                return np.array(result[0]['embedding'])
            return None
        except Exception as e:
            print(f"Error in DeepFace representation: {e}")
            return None
    
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

