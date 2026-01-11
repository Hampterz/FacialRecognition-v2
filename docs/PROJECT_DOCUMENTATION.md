# Facial Recognition System with Smart Attendance - Project Documentation

## 📋 Project Overview

This is a comprehensive **Facial Recognition System** built with Python that provides real-time face detection, recognition, and automated attendance tracking. The system features a modern graphical user interface and integrates with Google Sheets for automatic attendance management.

### Key Features

- **🎓 Multi-Model Face Detection**: Supports YOLOv11 (default), YOLOv8, RetinaFace, and DeepFace models
- **📹 Live Camera Recognition**: Real-time face recognition from webcam feed with camera controls
- **🎯 Smart Attendance System**: Automated attendance tracking with Google Sheets integration
  - Daily archiving of trained student names
  - Automatic date-based organization
  - Real-time attendance marking with duplicate prevention
- **📸 Automated Photo Capture**: Saves annotated attendance photos with bounding boxes and date stamps
- **🎨 Modern GUI**: Dark-themed, user-friendly interface built with Tkinter
- **🎭 Facial Analysis**: Emotion, age, gender, and race detection (with DeepFace)
- **🎙️ Voice Integration**: Real-time voice conversations with Google Gemini Live API
- **📁 Batch Training**: Support for image folders and video file processing
- **🔄 Accuracy Improvements**: Detection history system prevents false positives and stabilizes recognition

---

## 🏗️ System Architecture

### Technology Stack

**Core Technologies:**
- **Python 3.12.7** (Primary development language)
- **OpenCV (cv2)** - Camera access and image processing
- **face_recognition** - Face encoding and recognition
- **Tkinter** - GUI framework
- **NumPy** - Numerical operations
- **Pillow (PIL)** - Image manipulation

**Machine Learning Models:**
- **YOLOv11** - Latest YOLO architecture for face detection (default)
- **YOLOv8** - Stable YOLO variant
- **RetinaFace** - Deep learning model with facial landmarks
- **DeepFace** - Face recognition with emotion/age/gender analysis

**Integration Services:**
- **Google Sheets API** - Attendance tracking
- **Google Gemini Live API** - Voice conversations
- **gspread & oauth2client** - Google Sheets connectivity

### Project Structure

```S
facial-recognition/
│
├── app.py                      # Main GUI application (entry point)
├── attendance_sheet.py         # Google Sheets integration
├── detector.py                 # Training and recognition engine
├── yolo_face_detector.py       # YOLOv11 face detector
├── yolov8_detector.py          # YOLOv8 face detector
├── retinaface_detector.py      # RetinaFace detector
├── deepface_detector.py        # DeepFace detector with analysis
├── video_utils.py              # Video processing utilities
├── gemini_live_api.py          # Gemini API integration
│
├── training/                   # Training images (organized by person)
│   └── PersonName/
│       ├── img1.jpg
│       └── img2.jpg
│
├── output/                     # Generated encodings (model-specific)
│   ├── encodings_yolov11.pkl
│   ├── encodings_yolov8.pkl
│   ├── encodings_retinaface.pkl
│   ├── encodings_deepface.pkl
│   └── gemini_api_key.txt     # Gemini API key (if configured)
│
├── models/                     # Downloaded YOLO models
│   ├── yolov11n_face_detection.pt
│   └── yolov8_face_detection.pt
│
├── attendance_sheet.py         # Google Sheets integration (configure with your credentials)
├── attendance_sheet.py.example # Template file for credentials setup
├── SETUP_CREDENTIALS.md        # Detailed Google Sheets setup instructions
└── requirements.txt            # Python dependencies
```

---

## 🚀 How It Works

### 1. Face Recognition Pipeline

**Training Phase:**
1. User adds photos of individuals to the `training/` directory (organized by person name)
2. System extracts faces from images using selected detection model (YOLOv11, YOLOv8, etc.)
3. Face encodings are generated using `face_recognition` library (HOG or CNN model)
4. Encodings are saved to model-specific pickle files in `output/` directory
5. Each model maintains separate training data

**Recognition Phase:**
1. Camera captures video frames at real-time speed
2. Each frame is processed through the selected face detection model
3. Detected faces are encoded and compared against trained encodings
4. Recognition confidence scores are calculated using distance metrics
5. Recognized faces are displayed with bounding boxes and names
6. Recognition results are stabilized using detection history (prevents flickering)

### 2. Smart Attendance System

**Daily Initialization:**
1. System checks if it's a new day (date change detection, checked every minute)
2. If new day, resets the `seen_today` set
3. Archives **only trained student names** to Google Sheets (not all names from sheet):
   - Retrieves trained student names from current encodings
   - Finds last row with data in Column A
   - Creates new section 2 rows below previous data
   - Writes current date in Column C (DATE) on first row of new section
   - Writes all trained student names in Column A (Student) starting from that row
   - Each new day creates a separate section with its own date

**Recognition & Marking:**
1. Camera continuously processes frames
2. Face recognition runs on detected faces
3. Detection history tracks consistent identifications:
   - **Detection threshold**: Requires 8 consistent detections before marking attendance (prevents false positives)
   - **Display threshold**: Requires 3 consistent detections before showing name on screen (faster UI feedback)
   - **Timeout**: Detection history expires after 15 frames of not seeing a face (prevents stale data)
   - **Stabilization**: Separate `display_name` and `display_count` prevent name flickering in UI
4. When person is recognized with sufficient confidence:
   - Name appears in recognition overlay
   - If not already marked today, system:
     - Marks "Present" in Google Sheets (Column B - Status)
     - Saves annotated photo to date-based folder
     - Adds person to `seen_today` set (prevents duplicates)

**Photo Saving:**
- Photos saved to: `attendance_photos/YYYY-MM-DD/` (date-based subfolder, relative to project directory)
- Filename format: `PersonName.jpg` (or `PersonName_1.jpg`, `PersonName_2.jpg` if duplicates exist)
- Saved when attendance is marked (after 8 consistent detections)
- Uses full-resolution frame (not scaled version used for detection)
- Annotations included on saved photo:
  - Green bounding box around recognized face
  - Name label with checkmark (e.g., "PersonName ✓") with green background
  - Date stamp in top-right corner (YYYY-MM-DD format, black background for visibility)

**Google Sheets Structure:**
- **Column A (Student)**: Student names
- **Column B (Status)**: "Present" status
- **Column C (DATE)**: Date for each daily section

### 3. Detection History System

To improve accuracy and prevent false positives:
- **`detection_history`**: Dictionary tracking each detected face across frames
  - Key: Face location tuple (top, right, bottom, left) - rounded to handle small movements
  - Values: `name`, `count`, `display_name`, `display_count`, `last_seen`
  - `count`: Total consistent detections (for attendance marking threshold)
  - `display_count`: Separate counter for UI display (for name display threshold)
  - `last_seen`: Frame number when face was last detected (for timeout cleanup)
- **Stability mechanism**:
  - Count increases when same name detected at similar location
  - Count decreases faster when "Unknown" detected (prevents false positives)
  - Requires 8 consistent detections before marking attendance
  - Requires 3 consistent detections before showing name on screen
  - Uses separate display tracking to prevent UI flickering
- **Location matching**: Uses spatial proximity (rounded coordinates) to match faces across frames
- **Timeout cleanup**: Removes detection history for faces not seen in 15 frames

---

## 🛠️ Setup Instructions

### Prerequisites

1. **Python 3.12.7** (or 3.9+)
   - Download from [python.org](https://www.python.org/downloads/)
   - Ensure Python is added to PATH

2. **System Dependencies** (Windows):
   - CMake 4.2.1+ (for building dependencies)
   - Visual Studio Build Tools or MinGW (C compiler)

### Installation Steps

1. **Clone or Download the Repository**
   ```bash
   git clone <repository-url>
   cd facial-recognition
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   **Note**: Installation may take 10-15 minutes due to PyTorch and deep learning libraries.

3. **Verify Installation**
   ```bash
   python verify_setup.py
   ```

### Google Sheets Setup (for Smart Attendance)

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project

2. **Enable APIs**
   - Enable "Google Sheets API"
   - Enable "Google Drive API"

3. **Create Service Account**
   - Go to "IAM & Admin" → "Service Accounts"
   - Create new service account
   - Download JSON credentials file
   - Save as `smart-attendence-credentials.json` (or update path in `attendance_sheet.py`)

4. **Create Google Spreadsheet**
   - Create new Google Sheet
   - Share with service account email (from JSON file)
   - Copy Spreadsheet ID from URL
   - Update `SPREADSHEET_ID` in `attendance_sheet.py`

5. **Configure Spreadsheet Structure**
   - Set headers: Column A = "Student", Column B = "Status", Column C = "DATE"
   - System will auto-populate data when Smart Attendance runs
   - Each day creates a new section with date in Column C and student names in Column A
   - System marks "Present" in Column B when students are recognized

6. **Update attendance_sheet.py Configuration**
   - Open `attendance_sheet.py`
   - Replace `YOUR_SPREADSHEET_ID_HERE` with your actual Spreadsheet ID
   - Replace `path\to\your\service-account-credentials.json` with path to your JSON credentials file
   - See `SETUP_CREDENTIALS.md` for detailed setup instructions

### Run the Application

**Option 1: Double-click `run.bat` (Windows)**

**Option 2: Command line**
```bash
python app.py
```

---

## 📖 Usage Guide

### Training the Model

1. **Open the Application**
   - Launch `app.py`
   - Click "🎓 Train Model" on homepage

2. **Select Detection Model**
   - Choose from: YOLOv11 (default), YOLOv8, RetinaFace, DeepFace
   - Each model trains independently

3. **Add Training Data**
   - **Option A**: Click "📷 Add Photos" → Select multiple images
   - **Option B**: Click "📁 Import Folder" → Select folder with person subfolders
   - **Option C**: Click "🎬 Add Video" → Extract frames from video

4. **Train**
   - Enter person name for each set of photos
   - Click "🚀 Train Model"
   - Wait for training to complete (progress shown)

**Tips:**
- Use 5-10 photos per person for best results
- Include varied lighting and angles
- Higher resolution photos = better accuracy

### Live Recognition

1. **Start Live Camera**
   - Select model from dropdown (or use default YOLOv11)
   - Click "📹 Live Camera Recognition"
   - Allow camera permissions if prompted

2. **Use Camera Controls**
   - Flip horizontal/vertical
   - Rotate (0°, 90°, 180°, 270°)
   - Adjust recognition threshold in settings

3. **View Results**
   - Recognized faces show bounding boxes and names
   - With DeepFace: See emotion, age, gender analysis

### Smart Attendance

1. **Prerequisites**
   - Train model with student photos first (uses only trained student names for archiving)
   - Set up Google Sheets (see Setup Instructions)
   - Ensure credentials file is accessible

2. **Start Smart Attendance**
   - Click "📋 Smart Attendance" button
   - System automatically archives **trained student names** to Google Sheet for the day
   - Camera opens in attendance mode (uses YOLOv11 detection model automatically)

3. **Attendance Tracking**
   - Students appear in camera
   - System recognizes and marks "Present" in Google Sheet (Column B - Status)
   - Photos saved to date-based folders with annotations
   - Right sidebar shows real-time attendance status list
   - Status label displays total count of marked students

4. **Camera Controls** (Same as Live Recognition)
   - **Flip Horizontal** (↔️): Mirror the camera feed horizontally
   - **Flip Vertical** (↕️): Mirror the camera feed vertically
   - **Rotate** (🔄): Rotate camera 90° (0°, 90°, 180°, 270°)

5. **Control Buttons**
   - **📋 Check Spreadsheet**: Manually refresh attendance list from Google Sheet
     - Syncs with current spreadsheet data
     - Updates UI with students already marked present
     - Useful for checking if spreadsheet was updated externally
   - **🔄 Reset Attendance**: Clear today's tracking (allows re-marking students)
     - Resets the `seen_today` set
     - Clears the attendance list in UI
     - Does NOT clear Google Sheet data

6. **Daily Reset**
   - System automatically detects new day (checks every minute)
   - Creates new section in Google Sheet (2 rows below previous data)
   - Archives trained student names with current date
   - Resets `seen_today` set for new day

---

## 🔧 Technical Details

### Recognition Accuracy

**Thresholds & Parameters:**
- **Recognition threshold**: 0.40 (face_recognition distance threshold, tunable in code)
- **Required consistent detections**: 8 (for attendance marking - prevents false positives)
- **Required display detections**: 3 (for name display on screen - faster UI feedback)
- **Detection timeout**: 15 frames (removes detection history if face not seen)
- **Detection decay**: Fast decay on "Unknown" detections to prevent false positives
- **Frame processing**: Processes every 3rd frame (reduces CPU load)
- **Detection model**: YOLOv11 (enforced for Smart Attendance, same as default Live Recognition)

**Model Comparison:**
- **YOLOv11**: Best accuracy, fastest inference (recommended)
- **YOLOv8**: Stable, proven performance
- **RetinaFace**: Best for crowded scenes, facial landmarks
- **DeepFace**: Emotion/age/gender analysis, slower

### Performance Optimizations

1. **Frame Processing**
   - Process every 3rd frame (reduces CPU load)
   - Scale frames to 25% for detection (speeds up processing)
   - Scale coordinates back to full frame for display

2. **Detection History**
   - Tracks faces across frames
   - Prevents duplicate attendance marking
   - Stabilizes recognition display

3. **Google Sheets Updates**
   - Non-blocking updates (doesn't freeze camera feed)
   - Single update per student per day (prevents duplicate marks via `seen_today` set)
   - Updates Column B (Status) with "Present" when student recognized
   - Finds correct row by matching student name in Column A within today's date section
   - Error handling with detailed logging and user notifications
   - Check Spreadsheet button allows manual sync with Google Sheet data

### Error Handling

- **Camera access errors**: Graceful fallback messages
- **Google Sheets errors**: Detailed error logging, continues operation
- **Model loading errors**: Falls back to available models
- **Recognition errors**: Handles edge cases (no faces, multiple faces)

---

## 🎓 Educational Value

This project demonstrates:

1. **Computer Vision Concepts**
   - Face detection algorithms
   - Feature extraction and encoding
   - Distance metrics for similarity matching
   - Real-time video processing

2. **Machine Learning Integration**
   - Pre-trained model usage (YOLO, RetinaFace)
   - Transfer learning applications
   - Model comparison and evaluation

3. **Software Engineering**
   - GUI development with Tkinter
   - Multi-threading for non-blocking operations
   - API integration (Google Sheets, Gemini)
   - File system organization
   - Error handling and logging

4. **System Integration**
   - Camera hardware interfacing
   - Cloud service integration (Google APIs)
   - Data persistence (pickle, Google Sheets)
   - Real-time data synchronization

5. **User Experience Design**
   - Modern UI/UX principles
   - Responsive feedback systems
   - Progress indicators
   - Error messaging

---

## 🔒 Security & Privacy Considerations

1. **Credentials Management**
   - Service account JSON stored locally (not in repository)
   - Should be added to `.gitignore`
   - Never commit credentials to version control

2. **Data Storage**
   - Training images stored locally
   - Attendance photos stored locally
   - Google Sheets data synced to cloud (controlled access)

3. **Privacy**
   - All processing done locally (except Google Sheets sync)
   - No face data sent to external services (except Gemini API if used)
   - Users control their training data

---

## 🚀 Future Enhancements

Potential improvements:

- **Database Integration**: Replace Google Sheets with SQL database
- **Multi-Camera Support**: Track attendance across multiple locations
- **Analytics Dashboard**: Visualize attendance trends
- **Mobile App**: Companion app for remote monitoring
- **Cloud Deployment**: Web-based interface
- **Advanced Analytics**: Attendance patterns, predictions
- **Export Features**: PDF reports, CSV exports

---

## 📝 License & Credits

**Technologies Used:**
- YOLOv11: [AdamCodd/YOLOv11n-face-detection](https://huggingface.co/AdamCodd/YOLOv11n-face-detection)
- YOLOv8: [arnabdhar/YOLOv8-Face-Detection](https://huggingface.co/arnabdhar/YOLOv8-Face-Detection)
- RetinaFace: [serengil/retinaface](https://github.com/serengil/retinaface)
- DeepFace: [serengil/deepface](https://github.com/serengil/deepface)
- face_recognition: [ageitgey/face_recognition](https://github.com/ageitgey/face_recognition)

**APIs:**
- Google Sheets API
- Google Gemini Live API

---

## 📧 Contact & Support

For questions, issues, or contributions, please refer to the repository's issue tracker.

---

**Last Updated**: January 2025
**Version**: 1.0
**Author**: Sreyas

