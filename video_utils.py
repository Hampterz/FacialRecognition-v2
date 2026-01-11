"""
Video utilities for extracting frames from videos for training and testing.
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image


def extract_frames_from_video(video_path, output_dir, frames_per_second=1, max_frames=None):
    """
    Extract frames from a video file.
    
    Args:
        video_path: Path to video file
        output_dir: Directory to save extracted frames
        frames_per_second: How many frames to extract per second (default: 1)
        max_frames: Maximum number of frames to extract (None for all)
    
    Returns:
        Number of frames extracted
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps / frames_per_second) if frames_per_second > 0 else 1
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    frame_count = 0
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Extract frame at specified interval
        if frame_count % frame_interval == 0:
            if max_frames and saved_count >= max_frames:
                break
            
            # Save frame
            frame_path = output_dir / f"frame_{saved_count:05d}.jpg"
            cv2.imwrite(str(frame_path), frame)
            saved_count += 1
        
        frame_count += 1
    
    cap.release()
    return saved_count


def process_video_for_training(video_path, person_name, frames_per_second=1):
    """
    Extract frames from video and save to training directory.
    
    Args:
        video_path: Path to video file
        person_name: Name of the person in the video
        frames_per_second: Frames to extract per second
    
    Returns:
        Number of frames extracted
    """
    from app import TRAINING_DIR
    
    person_name = person_name.strip().replace(" ", "_")
    person_dir = TRAINING_DIR / person_name
    person_dir.mkdir(exist_ok=True)
    
    return extract_frames_from_video(video_path, person_dir, frames_per_second)


def get_video_frames(video_path, max_frames=None):
    """
    Get frames from video as numpy arrays.
    
    Args:
        video_path: Path to video file
        max_frames: Maximum frames to extract (None for all)
    
    Yields:
        Frame as numpy array (BGR format)
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    try:
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if max_frames and frame_count >= max_frames:
                break
            
            yield frame
            frame_count += 1
    finally:
        cap.release()

