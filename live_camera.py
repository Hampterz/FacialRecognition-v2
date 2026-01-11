# live_camera.py

import cv2
import face_recognition
import pickle
from pathlib import Path
import numpy as np

DEFAULT_ENCODINGS_PATH = Path("output/encodings.pkl")


def load_encodings(encodings_location: Path = DEFAULT_ENCODINGS_PATH):
    """Load face encodings from disk."""
    try:
        with encodings_location.open(mode="rb") as f:
            loaded_encodings = pickle.load(f)
        print(f"Loaded encodings for {len(set(loaded_encodings['names']))} person(s)")
        return loaded_encodings
    except FileNotFoundError:
        print(f"Error: Encodings file not found at {encodings_location}")
        print("Please train the model first using: python detector.py --train")
        return None


def recognize_face_in_frame(face_encoding, loaded_encodings):
    """Compare face encoding with known encodings and return best match."""
    from collections import Counter
    
    boolean_matches = face_recognition.compare_faces(
        loaded_encodings["encodings"], face_encoding, tolerance=0.6
    )
    votes = Counter(
        name
        for match, name in zip(boolean_matches, loaded_encodings["names"])
        if match
    )
    if votes:
        return votes.most_common(1)[0][0]
    return None


def run_live_recognition(model: str = "hog", camera_index: int = 0):
    """
    Run face recognition on live camera feed.
    
    Args:
        model: "hog" for CPU or "cnn" for GPU
        camera_index: Camera device index (usually 0 for default camera)
    """
    # Load encodings
    loaded_encodings = load_encodings()
    if loaded_encodings is None:
        return
    
    # Initialize camera
    video_capture = cv2.VideoCapture(camera_index)
    
    if not video_capture.isOpened():
        print(f"Error: Could not open camera {camera_index}")
        return
    
    print("Camera started. Press 'q' to quit.")
    
    # Process frames
    process_this_frame = True
    
    while True:
        # Grab a single frame of video
        ret, frame = video_capture.read()
        
        if not ret:
            print("Failed to grab frame")
            break
        
        # Resize frame for faster processing (optional, but recommended)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Only process every other frame to save time
        if process_this_frame:
            # Find all faces and face encodings in the current frame
            face_locations = face_recognition.face_locations(rgb_small_frame, model=model)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                name = recognize_face_in_frame(face_encoding, loaded_encodings)
                if name:
                    face_names.append(name)
                else:
                    face_names.append("Unknown")
        
        process_this_frame = not process_this_frame
        
        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            
            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            
            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
        
        # Display the resulting image
        cv2.imshow('Face Recognition', frame)
        
        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()
    print("Camera released.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Live face recognition from camera")
    parser.add_argument(
        "-m",
        action="store",
        default="hog",
        choices=["hog", "cnn"],
        help="Which model to use: hog (CPU), cnn (GPU)",
    )
    parser.add_argument(
        "-c",
        action="store",
        type=int,
        default=0,
        help="Camera index (default: 0)",
    )
    args = parser.parse_args()
    
    run_live_recognition(model=args.m, camera_index=args.c)

