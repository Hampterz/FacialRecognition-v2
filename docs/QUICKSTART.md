# Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Fix Installation Issues (If Needed)

If you're getting numpy/dlib installation errors, run:

```bash
python install_fix.py
```

Or manually install:
```bash
pip install --upgrade pip
pip install cmake
pip install numpy
pip install dlib
pip install face-recognition opencv-python Pillow
```

### 2. Launch the Application

```bash
python app.py
```

### 3. Train and Use

1. **Add People:**
   - Click "🎓 Train Model"
   - Enter name: "Your Name"
   - Click "📷 Add Photos"
   - Select 5-10 photos of yourself
   - Repeat for other people

2. **Train:**
   - Click "🚀 Train Model"
   - Wait for "Training complete!" message

3. **Recognize:**
   - Click "📹 Live Camera Recognition"
   - Walk in front of camera
   - Your name will appear!

## 📸 Tips for Best Results

- **Use 5-10 clear photos per person**
- **Front-facing photos work best**
- **Good lighting is important**
- **Different angles and expressions help**
- **Avoid blurry or dark photos**

## ❓ Troubleshooting

**Camera not opening?**
- Check Settings → Camera Index (try 0, 1, or 2)
- Make sure no other app is using the camera

**Not recognizing you?**
- Add more training photos
- Make sure photos are clear and well-lit
- Retrain the model after adding photos

**Installation errors?**
- See SETUP.md for detailed instructions
- Make sure CMake and C++ compiler are installed

