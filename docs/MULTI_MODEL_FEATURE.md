# 🎯 Multi-Model Face Detection Feature

## Overview

The face recognition system now supports **multiple face detection models** with **separate training data** for each model. You can switch between models and train each one independently.

## Supported Models

### 1. **YOLOv11** (Default)
- **Source**: [AdamCodd/YOLOv11n-face-detection](https://huggingface.co/AdamCodd/YOLOv11n-face-detection)
- **Performance**: Easy AP: 94.2%, Medium AP: 92.1%, Hard AP: 81.0%
- **Best for**: Latest technology, best accuracy
- **Training file**: `output/encodings_yolov11.pkl`

### 2. **YOLOv8**
- **Source**: [arnabdhar/YOLOv8-Face-Detection](https://huggingface.co/arnabdhar/YOLOv8-Face-Detection)
- **Best for**: Stable, proven performance
- **Training file**: `output/encodings_yolov8.pkl`

### 3. **RetinaFace**
- **Source**: [serengil/retinaface](https://github.com/serengil/retinaface)
- **Features**: Deep learning with facial landmarks
- **Best for**: Crowded scenes, facial landmark detection
- **Training file**: `output/encodings_retinaface.pkl`
- **Install**: `pip install retina-face`

## Key Features

### ✅ Separate Training Data
- Each model has its own training file
- Train YOLOv11 independently from YOLOv8
- Train RetinaFace separately
- No conflicts between models

### ✅ Model Selection Dropdown
- Select model in training page
- Switch models anytime
- Each model shows its training status

### ✅ Independent Training
- Click "Train Model" for selected model
- Only trains the currently selected model
- Other models' training data remains untouched

### ✅ Automatic Model Switching
- Recognition uses currently selected model
- Live camera uses selected model
- Test image uses selected model

## How to Use

### 1. Select a Model
1. Go to **Training Page**
2. Use the **"Face Detection Model"** dropdown
3. Choose: YOLOv11, YOLOv8, or RetinaFace

### 2. Train the Model
1. Add people and photos (same for all models)
2. Select your desired model from dropdown
3. Click **"Train Model"**
4. Training data saved to model-specific file

### 3. Switch Models
1. Select different model from dropdown
2. Status updates automatically
3. Shows training status for that model
4. Recognition uses selected model

## File Structure

```
output/
├── encodings_yolov11.pkl      # YOLOv11 training data
├── encodings_yolov8.pkl       # YOLOv8 training data
├── encodings_retinaface.pkl   # RetinaFace training data
├── processed_files_yolov11.pkl
├── processed_files_yolov8.pkl
└── processed_files_retinaface.pkl
```

## Installation

### For YOLOv8 and YOLOv11:
Already included in requirements.txt

### For RetinaFace:
```bash
pip install retina-face
```

## Benefits

1. **Compare Models**: Test which model works best for your use case
2. **Flexibility**: Use different models for different scenarios
3. **No Data Loss**: Each model's training is preserved separately
4. **Easy Switching**: Change models with a dropdown
5. **Independent Training**: Train one model without affecting others

## Example Workflow

1. **Train YOLOv11**:
   - Select "yolov11" from dropdown
   - Add people and photos
   - Click "Train Model"
   - YOLOv11 now recognizes those people

2. **Train YOLOv8**:
   - Select "yolov8" from dropdown
   - Same people/photos (or different)
   - Click "Train Model"
   - YOLOv8 now recognizes those people

3. **Compare**:
   - Switch between models
   - Test recognition accuracy
   - Use the best model for your needs

## Notes

- **Training data is shared**: All models use the same `training/` folder
- **Encodings are separate**: Each model creates its own encodings
- **Incremental training**: Works for each model independently
- **Model caching**: Detectors are cached for performance

## Troubleshooting

### RetinaFace not available?
```bash
pip install retina-face
```

### Model not loading?
- Check internet connection (first download)
- Models are cached in `models/` folder
- Check console for error messages

### Training not working?
- Make sure you've selected a model
- Check that training data exists
- Verify model is selected before training

---

**Enjoy the flexibility of multiple face detection models!** 🚀

