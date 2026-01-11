"""
DeepFace Calibration Module
Allows fine-tuning/correction of DeepFace predictions using personal training data.
"""

import pickle
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import json
import cv2
from PIL import Image
import os

class DeepFaceCalibrator:
    """
    Calibrates DeepFace predictions using personal training data.
    Collects ground truth labels and learns correction mappings.
    """
    
    def __init__(self, calibration_file: Optional[Path] = None):
        """
        Initialize the calibrator.
        
        Args:
            calibration_file: Path to save/load calibration data
        """
        self.calibration_file = calibration_file or Path("output/deepface_calibration.pkl")
        self.calibration_data = {
            'emotion_corrections': {},  # {person_name: {predicted: actual}}
            'age_corrections': {},      # {person_name: [(predicted, actual), ...]}
            'gender_corrections': {},   # {person_name: {predicted: actual}}
            'race_corrections': {},     # {person_name: {predicted: actual}}
        }
        self.load_calibration()
    
    def load_calibration(self):
        """Load calibration data from file."""
        if self.calibration_file.exists():
            try:
                with open(self.calibration_file, 'rb') as f:
                    self.calibration_data = pickle.load(f)
                print(f"✓ Loaded calibration data from {self.calibration_file}")
            except Exception as e:
                print(f"Error loading calibration: {e}")
    
    def save_calibration(self):
        """Save calibration data to file."""
        try:
            self.calibration_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.calibration_file, 'wb') as f:
                pickle.dump(self.calibration_data, f)
            print(f"✓ Saved calibration data to {self.calibration_file}")
        except Exception as e:
            print(f"Error saving calibration: {e}")
    
    def add_training_sample(self, person_name: str, deepface_result: Dict, 
                           ground_truth: Dict):
        """
        Add a training sample for calibration.
        
        Args:
            person_name: Name of the person
            deepface_result: Result from DeepFace.analyze()
            ground_truth: Ground truth values {'emotion': 'happy', 'age': 25, 'gender': 'Man', 'race': 'white'}
        """
        # Emotion correction
        if 'emotion' in ground_truth:
            predicted_emotion = deepface_result.get('dominant_emotion', '')
            actual_emotion = ground_truth['emotion']
            if person_name not in self.calibration_data['emotion_corrections']:
                self.calibration_data['emotion_corrections'][person_name] = {}
            if predicted_emotion not in self.calibration_data['emotion_corrections'][person_name]:
                self.calibration_data['emotion_corrections'][person_name][predicted_emotion] = actual_emotion
        
        # Age correction (store multiple samples for averaging)
        if 'age' in ground_truth:
            predicted_age = deepface_result.get('age', 0)
            actual_age = ground_truth['age']
            if person_name not in self.calibration_data['age_corrections']:
                self.calibration_data['age_corrections'][person_name] = []
            self.calibration_data['age_corrections'][person_name].append(
                (predicted_age, actual_age)
            )
        
        # Gender correction
        if 'gender' in ground_truth:
            predicted_gender = deepface_result.get('dominant_gender', '')
            actual_gender = ground_truth['gender']
            if person_name not in self.calibration_data['gender_corrections']:
                self.calibration_data['gender_corrections'][person_name] = {}
            if predicted_gender not in self.calibration_data['gender_corrections'][person_name]:
                self.calibration_data['gender_corrections'][person_name][predicted_gender] = actual_gender
        
        # Race correction
        if 'race' in ground_truth:
            predicted_race = deepface_result.get('dominant_race', '')
            actual_race = ground_truth['race']
            if person_name not in self.calibration_data['race_corrections']:
                self.calibration_data['race_corrections'][person_name] = {}
            if predicted_race not in self.calibration_data['race_corrections'][person_name]:
                self.calibration_data['race_corrections'][person_name][predicted_race] = actual_race
        
        self.save_calibration()
    
    def calibrate_emotion(self, person_name: str, predicted_emotion: str) -> str:
        """Apply emotion correction if available."""
        if person_name in self.calibration_data['emotion_corrections']:
            corrections = self.calibration_data['emotion_corrections'][person_name]
            if predicted_emotion in corrections:
                return corrections[predicted_emotion]
        return predicted_emotion
    
    def calibrate_age(self, person_name: str, predicted_age: int) -> int:
        """
        Apply age correction using average offset.
        Uses DeepFace model prediction as base, then applies personal calibration.
        """
        if person_name in self.calibration_data['age_corrections']:
            samples = self.calibration_data['age_corrections'][person_name]
            if len(samples) >= 1:  # Use even 1 sample (reduced from 3 for better responsiveness)
                offsets = [actual - predicted for predicted, actual in samples]
                avg_offset = int(np.mean(offsets))
                calibrated_age = max(0, predicted_age + avg_offset)
                return calibrated_age
        # Return DeepFace model prediction if no calibration data
        return predicted_age
    
    def calibrate_gender(self, person_name: str, predicted_gender: str) -> str:
        """Apply gender correction if available."""
        if person_name in self.calibration_data['gender_corrections']:
            corrections = self.calibration_data['gender_corrections'][person_name]
            if predicted_gender in corrections:
                return corrections[predicted_gender]
        return predicted_gender
    
    def calibrate_race(self, person_name: str, predicted_race: str) -> str:
        """Apply race correction if available."""
        if person_name in self.calibration_data['race_corrections']:
            corrections = self.calibration_data['race_corrections'][person_name]
            if predicted_race in corrections:
                return corrections[predicted_race]
        return predicted_race
    
    def calibrate_result(self, person_name: str, deepface_result: Dict) -> Dict:
        """
        Apply all calibrations to a DeepFace result.
        
        This combines:
        1. Pre-trained DeepFace model predictions (base predictions)
        2. Personal calibration data (corrections learned from your training images)
        
        Args:
            person_name: Name of the person
            deepface_result: Result from DeepFace.analyze() (pre-trained model predictions)
            
        Returns:
            Calibrated result dictionary (DeepFace predictions + personal corrections)
        """
        # Start with DeepFace pre-trained model predictions
        calibrated = deepface_result.copy()
        
        # Apply personal calibration corrections if available
        # This uses your training data to correct the model's predictions
        if 'dominant_emotion' in calibrated:
            original_emotion = calibrated['dominant_emotion']
            calibrated['dominant_emotion'] = self.calibrate_emotion(
                person_name, calibrated['dominant_emotion']
            )
            # Log if calibration was applied
            if calibrated['dominant_emotion'] != original_emotion:
                print(f"Calibration: emotion '{original_emotion}' -> '{calibrated['dominant_emotion']}' for {person_name}")
        
        if 'age' in calibrated:
            original_age = int(calibrated['age'])
            calibrated['age'] = self.calibrate_age(
                person_name, original_age
            )
            # Log if calibration was applied
            if calibrated['age'] != original_age:
                print(f"Calibration: age {original_age} -> {calibrated['age']} for {person_name}")
        
        if 'dominant_gender' in calibrated:
            original_gender = calibrated['dominant_gender']
            calibrated['dominant_gender'] = self.calibrate_gender(
                person_name, calibrated['dominant_gender']
            )
            # Log if calibration was applied
            if calibrated['dominant_gender'] != original_gender:
                print(f"Calibration: gender '{original_gender}' -> '{calibrated['dominant_gender']}' for {person_name}")
        
        if 'dominant_race' in calibrated:
            original_race = calibrated['dominant_race']
            calibrated['dominant_race'] = self.calibrate_race(
                person_name, calibrated['dominant_race']
            )
            # Log if calibration was applied
            if calibrated['dominant_race'] != original_race:
                print(f"Calibration: race '{original_race}' -> '{calibrated['dominant_race']}' for {person_name}")
        
        return calibrated
    
    def get_calibration_stats(self) -> Dict:
        """Get statistics about calibration data."""
        stats = {
            'people_calibrated': set(),
            'emotion_samples': 0,
            'age_samples': 0,
            'gender_samples': 0,
            'race_samples': 0,
        }
        
        for person_name in self.calibration_data['emotion_corrections']:
            stats['people_calibrated'].add(person_name)
            stats['emotion_samples'] += len(self.calibration_data['emotion_corrections'][person_name])
        
        for person_name in self.calibration_data['age_corrections']:
            stats['people_calibrated'].add(person_name)
            stats['age_samples'] += len(self.calibration_data['age_corrections'][person_name])
        
        for person_name in self.calibration_data['gender_corrections']:
            stats['people_calibrated'].add(person_name)
            stats['gender_samples'] += len(self.calibration_data['gender_corrections'][person_name])
        
        for person_name in self.calibration_data['race_corrections']:
            stats['people_calibrated'].add(person_name)
            stats['race_samples'] += len(self.calibration_data['race_corrections'][person_name])
        
        stats['people_calibrated'] = len(stats['people_calibrated'])
        return stats
    
    def train_from_person_folder(self, person_folder: Path, progress_callback=None) -> Dict:
        """
        Train calibration from a person-based folder structure.
        
        Folder structure:
        person_folder/ (e.g., "sreyas/")
          ├── emotion/
          │   ├── happy/ (images of happy faces)
          │   ├── sad/ (images of sad faces)
          │   ├── angry/ (images of angry faces)
          │   ├── surprise/ (images of surprised faces)
          │   ├── fear/ (images of fearful faces)
          │   ├── disgust/ (images of disgusted faces)
          │   └── neutral/ (images of neutral faces)
          ├── race/
          │   ├── asian/ (images of asian faces)
          │   ├── white/ (images of white faces)
          │   └── etc.
          └── age/
              ├── 25/ (images at age 25)
              ├── 30/ (images at age 30)
              └── etc.
        
        Args:
            person_folder: Path to person folder (e.g., "training/sreyas/")
            progress_callback: Optional callback function(current, total, message)
            
        Returns:
            Dictionary with training statistics
        """
        from deepface_detector import DeepFaceDetector
        
        if not person_folder.exists():
            raise ValueError(f"Person folder does not exist: {person_folder}")
        
        # Extract person name from folder name
        person_name = person_folder.name
        
        detector = DeepFaceDetector()
        stats = {
            'emotion_samples': 0,
            'race_samples': 0,
            'age_samples': 0,
            'errors': []
        }
        
        # Supported values
        valid_emotions = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
        valid_races = ['asian', 'indian', 'black', 'white', 'middle eastern', 'latino hispanic']
        
        # Process emotion folder
        emotion_folder = person_folder / "emotion"
        if emotion_folder.exists() and emotion_folder.is_dir():
            emotion_dirs = [d for d in emotion_folder.iterdir() if d.is_dir()]
            total_emotion = sum(len(list(d.glob('*.[jp][pn]g'))) + len(list(d.glob('*.jpeg'))) for d in emotion_dirs)
            processed_emotion = 0
            
            for emotion_dir in emotion_dirs:
                emotion_label = emotion_dir.name.lower()
                if emotion_label not in valid_emotions:
                    stats['errors'].append(f"Invalid emotion folder: {emotion_label} (skipping)")
                    continue
                
                image_files = list(emotion_dir.glob('*.[jp][pn]g')) + list(emotion_dir.glob('*.jpeg'))
                for img_path in image_files:
                    try:
                        result = detector.analyze_face(str(img_path), actions=['emotion'])
                        if result:
                            ground_truth = {'emotion': emotion_label}
                            self.add_training_sample(person_name, result, ground_truth)
                            stats['emotion_samples'] += 1
                            processed_emotion += 1
                            
                            if progress_callback:
                                progress_callback(processed_emotion, total_emotion, 
                                                 f"Processing {person_name} emotion: {emotion_label}")
                    except Exception as e:
                        stats['errors'].append(f"Error processing {img_path}: {str(e)}")
        
        # Process race folder
        race_folder = person_folder / "race"
        if race_folder.exists() and race_folder.is_dir():
            race_dirs = [d for d in race_folder.iterdir() if d.is_dir()]
            total_race = sum(len(list(d.glob('*.[jp][pn]g'))) + len(list(d.glob('*.jpeg'))) for d in race_dirs)
            processed_race = 0
            
            for race_dir in race_dirs:
                race_label = race_dir.name.lower()
                # Normalize race labels
                race_mapping = {
                    'asian': 'asian',
                    'indian': 'indian',
                    'black': 'black',
                    'white': 'white',
                    'middle eastern': 'middle eastern',
                    'latino': 'latino hispanic',
                    'hispanic': 'latino hispanic',
                    'latino hispanic': 'latino hispanic'
                }
                race_label = race_mapping.get(race_label, race_label)
                
                if race_label not in valid_races:
                    stats['errors'].append(f"Invalid race folder: {race_dir.name} (skipping)")
                    continue
                
                image_files = list(race_dir.glob('*.[jp][pn]g')) + list(race_dir.glob('*.jpeg'))
                for img_path in image_files:
                    try:
                        result = detector.analyze_face(str(img_path), actions=['race'])
                        if result:
                            ground_truth = {'race': race_label}
                            self.add_training_sample(person_name, result, ground_truth)
                            stats['race_samples'] += 1
                            processed_race += 1
                            
                            if progress_callback:
                                progress_callback(processed_race, total_race, 
                                                 f"Processing {person_name} race: {race_label}")
                    except Exception as e:
                        stats['errors'].append(f"Error processing {img_path}: {str(e)}")
        
        # Process age folder
        age_folder = person_folder / "age"
        if age_folder.exists() and age_folder.is_dir():
            age_dirs = [d for d in age_folder.iterdir() if d.is_dir()]
            total_age = sum(len(list(d.glob('*.[jp][pn]g'))) + len(list(d.glob('*.jpeg'))) for d in age_dirs)
            processed_age = 0
            
            for age_dir in age_dirs:
                try:
                    age_label = int(age_dir.name)
                    if age_label < 0 or age_label > 120:
                        stats['errors'].append(f"Invalid age folder: {age_label} (must be 0-120)")
                        continue
                except ValueError:
                    stats['errors'].append(f"Invalid age folder name (must be number): {age_dir.name}")
                    continue
                
                image_files = list(age_dir.glob('*.[jp][pn]g')) + list(age_dir.glob('*.jpeg'))
                for img_path in image_files:
                    try:
                        result = detector.analyze_face(str(img_path), actions=['age'])
                        if result:
                            ground_truth = {'age': age_label}
                            self.add_training_sample(person_name, result, ground_truth)
                            stats['age_samples'] += 1
                            processed_age += 1
                            
                            if progress_callback:
                                progress_callback(processed_age, total_age, 
                                                 f"Processing {person_name} age: {age_label}")
                    except Exception as e:
                        stats['errors'].append(f"Error processing {img_path}: {str(e)}")
        
        self.save_calibration()
        return stats


def create_calibration_ui():
    """
    Helper function to create a simple UI for adding calibration data.
    This can be integrated into the main app.
    """
    print("""
    ========================================
    DeepFace Calibration Tool
    ========================================
    
    To improve accuracy for your face, you need to provide ground truth labels.
    
    Usage:
    1. Run DeepFace analysis on your training images
    2. For each image, provide the correct values:
       - Emotion: happy, sad, angry, surprise, fear, disgust, neutral
       - Age: Your actual age
       - Gender: Man or Woman
       - Race: white, black, asian, indian, latino, middle eastern
    
    3. The calibrator will learn the corrections and apply them automatically.
    
    Example:
    from deepface_calibration import DeepFaceCalibrator
    from deepface_detector import DeepFaceDetector
    
    detector = DeepFaceDetector()
    calibrator = DeepFaceCalibrator()
    
    # Analyze an image
    result = detector.analyze_face("your_photo.jpg")
    
    # Add ground truth
    ground_truth = {
        'emotion': 'happy',
        'age': 25,
        'gender': 'Man',
        'race': 'asian'
    }
    
    calibrator.add_training_sample("YourName", result, ground_truth)
    
    # Use calibrated results
    calibrated = calibrator.calibrate_result("YourName", result)
    """)

if __name__ == "__main__":
    create_calibration_ui()

