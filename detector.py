# detector.py

import argparse
import pickle
from collections import Counter
from pathlib import Path

import face_recognition
from PIL import Image, ImageDraw
import numpy as np
from yolo_face_detector import get_detector

DEFAULT_ENCODINGS_PATH = Path("output/encodings.pkl")
BOUNDING_BOX_COLOR = "blue"
TEXT_COLOR = "white"

Path("training").mkdir(exist_ok=True)
Path("output").mkdir(exist_ok=True)
Path("validation").mkdir(exist_ok=True)


def convert_image_to_rgb(image_path):
    """Convert image to RGB format."""
    # Load image using PIL for better compatibility
    pil_image = Image.open(image_path)
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    return np.array(pil_image, dtype=np.uint8)


def encode_known_faces(
    model: str = "hog", encodings_location: Path = DEFAULT_ENCODINGS_PATH
) -> None:
    """
    Load training images, detect faces, and create encodings.
    Training images should be organized in subdirectories named after each person.
    """
    names = []
    encodings = []
    processed_count = 0
    error_count = 0
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.JPG', '.JPEG', '.PNG', '.BMP'}

    for filepath in Path("training").glob("*/*"):
        if filepath.is_file() and filepath.suffix in image_extensions:
            name = filepath.parent.name
            try:
                # Convert image to RGB format
                image = convert_image_to_rgb(filepath)
                
                # Detect faces using YOLOv8
                detector = get_detector()
                face_locations = detector.detect_faces(image)
                
                if not face_locations:
                    print(f"No face found in {filepath.name}")
                    error_count += 1
                    continue
                
                face_encodings = face_recognition.face_encodings(image, face_locations)
                
                if not face_encodings:
                    print(f"Failed to encode face in {filepath.name}")
                    error_count += 1
                    continue

                for encoding in face_encodings:
                    names.append(name)
                    encodings.append(encoding)
                
                processed_count += 1
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
                error_count += 1

    if not names:
        print(f"\nERROR: No faces found in any training images!")
        print(f"Processed: {processed_count} files, Errors: {error_count} files")
        return

    name_encodings = {"names": names, "encodings": encodings}
    with encodings_location.open(mode="wb") as f:
        pickle.dump(name_encodings, f)
    
    print(f"\n✓ Encoded {len(names)} face(s) from {len(set(names))} person(s)")
    print(f"✓ Successfully processed {processed_count} image(s)")
    if error_count > 0:
        print(f"⚠ {error_count} image(s) had issues")


def _recognize_face(unknown_encoding, loaded_encodings):
    """Compare unknown face encoding with known encodings and return best match."""
    boolean_matches = face_recognition.compare_faces(
        loaded_encodings["encodings"], unknown_encoding
    )
    votes = Counter(
        name
        for match, name in zip(boolean_matches, loaded_encodings["names"])
        if match
    )
    if votes:
        return votes.most_common(1)[0][0]


def recognize_faces(
    image_location: str,
    model: str = "hog",
    encodings_location: Path = DEFAULT_ENCODINGS_PATH,
) -> None:
    """Recognize faces in an image and display results."""
    with encodings_location.open(mode="rb") as f:
        loaded_encodings = pickle.load(f)

    # Convert image to RGB format
    input_image = convert_image_to_rgb(image_location)

    # Detect faces using YOLOv8
    detector = get_detector()
    input_face_locations = detector.detect_faces(input_image)
    input_face_encodings = face_recognition.face_encodings(
        input_image, input_face_locations
    )

    pillow_image = Image.fromarray(input_image)
    draw = ImageDraw.Draw(pillow_image)

    for bounding_box, unknown_encoding in zip(
        input_face_locations, input_face_encodings
    ):
        name = _recognize_face(unknown_encoding, loaded_encodings)
        if not name:
            name = "Unknown"
        _display_face(draw, bounding_box, name)

    del draw
    pillow_image.show()


def _display_face(draw, bounding_box, name):
    """Draw bounding box and label on the image."""
    top, right, bottom, left = bounding_box
    draw.rectangle(((left, top), (right, bottom)), outline=BOUNDING_BOX_COLOR)
    text_left, text_top, text_right, text_bottom = draw.textbbox(
        (left, bottom), name
    )
    draw.rectangle(
        ((text_left, text_top), (text_right, text_bottom)),
        fill="blue",
        outline="blue",
    )
    draw.text(
        (text_left, text_top),
        name,
        fill="white",
    )


def validate(model: str = "hog"):
    """Validate the model against validation images."""
    for filepath in Path("validation").rglob("*"):
        if filepath.is_file():
            recognize_faces(
                image_location=str(filepath.absolute()), model=model
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recognize faces in an image")
    parser.add_argument("--train", action="store_true", help="Train on input data")
    parser.add_argument(
        "--validate", action="store_true", help="Validate trained model"
    )
    parser.add_argument(
        "--test", action="store_true", help="Test the model with an unknown image"
    )
    parser.add_argument(
        "-m",
        action="store",
        default="hog",
        choices=["hog", "cnn"],
        help="Which model to use for training: hog (CPU), cnn (GPU)",
    )
    parser.add_argument(
        "-f", action="store", help="Path to an image with an unknown face"
    )
    args = parser.parse_args()

    if args.train:
        encode_known_faces(model=args.m)
    if args.validate:
        validate(model=args.m)
    if args.test:
        recognize_faces(image_location=args.f, model=args.m)

