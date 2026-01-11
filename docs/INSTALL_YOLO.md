# Installing YOLOv8 Face Detection

## Quick Install

```bash
pip install ultralytics huggingface-hub supervision torch torchvision
```

## What Changed

We've replaced dlib face detection with **YOLOv8 Face Detection** from Hugging Face:
- ✅ No more dlib compatibility issues
- ✅ Works with Python 3.12
- ✅ More accurate face detection
- ✅ Faster and more modern

## How It Works

1. **Face Detection**: Uses YOLOv8 (from Hugging Face) to detect faces
2. **Face Recognition**: Still uses face_recognition library for encoding and matching

## First Run

On first run, the model will be automatically downloaded from Hugging Face (~50MB).
This only happens once.

## Requirements

- ultralytics>=8.0.0
- huggingface-hub>=0.16.0
- supervision>=0.18.0
- face-recognition (for encoding, not detection)
- torch and torchvision (for YOLOv8)

## Model Source

Model: [arnabdhar/YOLOv8-Face-Detection](https://huggingface.co/arnabdhar/YOLOv8-Face-Detection)
- Fine-tuned on 10k+ face images
- High accuracy face detection
- Works on CPU and GPU

