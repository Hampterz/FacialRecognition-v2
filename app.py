# app.py - Main GUI Application for Face Recognition System (Modern Dark Theme)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from typing import Optional
import cv2
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageFont
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("WARNING: face_recognition not available. Install dlib to enable face recognition.")
    print("See INSTALL_DLIB_WINDOWS.md for installation instructions.")
import pickle
from pathlib import Path
from collections import Counter
import shutil
import os
import numpy as np
from datetime import date, datetime
from yolo_face_detector import YOLOFaceDetector
from yolov8_detector import YOLOv8FaceDetector
from retinaface_detector import RetinaFaceDetector
from deepface_detector import DeepFaceDetector
from deepface_calibration import DeepFaceCalibrator
from video_utils import extract_frames_from_video, process_video_for_training, get_video_frames
from gemini_live_api import GeminiLiveAPI
try:
    from attendance_sheet import mark_present, get_present_students
    ATTENDANCE_AVAILABLE = True
except ImportError as e:
    ATTENDANCE_AVAILABLE = False
    print(f"Warning: attendance_sheet not available. Smart Attendance will not work.\nError: {e}")

# Model-specific encoding paths
ENCODINGS_PATHS = {
    "yolov8": Path("output/encodings_yolov8.pkl"),
    "yolov11": Path("output/encodings_yolov11.pkl"),
    "retinaface": Path("output/encodings_retinaface.pkl"),
    "deepface": Path("output/encodings_deepface.pkl"),
}

# Processed files paths for each model
PROCESSED_FILES_PATHS = {
    "yolov8": Path("output/processed_files_yolov8.pkl"),
    "yolov11": Path("output/processed_files_yolov11.pkl"),
    "retinaface": Path("output/processed_files_retinaface.pkl"),
    "deepface": Path("output/processed_files_deepface.pkl"),
}

# Default model
DEFAULT_MODEL = "yolov11"
TRAINING_DIR = Path("training")
OUTPUT_DIR = Path("output")
VALIDATION_DIR = Path("validation")

# Ensure directories exist
TRAINING_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
VALIDATION_DIR.mkdir(exist_ok=True)

# Modern Minimal Dark Theme Colors
COLORS = {
    "bg_primary": "#0f0f0f",      # Pure dark background
    "bg_secondary": "#1a1a1a",    # Elevated card background
    "bg_tertiary": "#252525",     # Input field background
    "bg_hover": "#2a2a2a",        # Hover state
    "accent_blue": "#3b82f6",     # Modern blue
    "accent_green": "#10b981",    # Modern green
    "accent_purple": "#8b5cf6",   # Modern purple
    "accent_orange": "#f59e0b",   # Modern orange
    "accent_pink": "#ec4899",     # Modern pink
    "text_primary": "#ffffff",    # Pure white
    "text_secondary": "#a1a1aa",  # Muted gray
    "text_tertiary": "#71717a",   # Very muted gray
    "border": "#27272a",           # Subtle border
    "border_light": "#3f3f46",    # Lighter border
    "success": "#10b981",         # Success green
    "warning": "#f59e0b",         # Warning orange
    "error": "#ef4444",           # Error red
    "shadow": "#000000",          # Shadow color
}


class ModernButton(tk.Button):
    """Modern minimalistic button with smooth hover effects."""
    def __init__(self, parent, **kwargs):
        # Extract button properties
        self.button_text = kwargs.get('text', 'Button')
        self.text_color = "#ffffff"  # White text
        self.bg_color = "#1a1a1a"  # Dark background
        self.hover_bg = "#2a2a2a"  # Lighter on hover
        self.active_bg = "#3a3a3a"  # Even lighter when pressed
        self.button_font = kwargs.get('font', ("Segoe UI", 14, "normal"))
        
        # Handle width - if it's a small number (<50), treat as character width, else pixels
        width_arg = kwargs.get('width', None)
        if width_arg and width_arg < 50:
            # Character width - convert to pixels (approx 8 pixels per character)
            self.button_width = max(120, width_arg * 8)
        else:
            self.button_width = width_arg if width_arg else None
        
        # Handle height
        self.button_height = 48  # Fixed modern height
        
        self.radius = 8  # Subtle rounded corners
        
        # Remove custom properties from kwargs
        for key in ['text', 'bg', 'fg', 'font', 'width', 'height', 'pady', 'padx']:
            kwargs.pop(key, None)
        
        # Set default button properties - use parent background
        parent_bg = parent.cget('bg') if hasattr(parent, 'cget') else COLORS.get('bg_primary', '#1e1e1e')
        kwargs['relief'] = tk.FLAT
        kwargs['bd'] = 0
        kwargs['cursor'] = 'hand2'
        kwargs['borderwidth'] = 0
        kwargs['highlightthickness'] = 0
        kwargs['bg'] = parent_bg  # Match parent background
        kwargs['activebackground'] = parent_bg
        kwargs['highlightbackground'] = parent_bg
        
        # Store command before calling super
        self.command = kwargs.get('command', None)
        kwargs.pop('command', None)
        
        super().__init__(parent, **kwargs)
        
        # Create button images immediately
        self.default_image = self._create_button_image(self.bg_color)
        self.hover_image = self._create_button_image(self.hover_bg)
        self.active_image = self._create_button_image(self.active_bg)
        
        # Set initial image and text
        self.config(image=self.default_image, compound='center', text='')
        
        # Update images when widget is resized
        self.bind("<Configure>", self._on_configure)
    
    def _on_configure(self, e):
        """Recreate images when widget is resized."""
        if e.width > 1 and e.height > 1:  # Only if actually sized
            self.default_image = self._create_button_image(self.bg_color)
            self.hover_image = self._create_button_image(self.hover_bg)
            self.active_image = self._create_button_image(self.active_bg)
            self.config(image=self.default_image)
        
        # Bind events
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        
        # Set command
        if self.command:
            self.config(command=self.command)
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _create_button_image(self, bg_color):
        """Create modern minimalistic button image that fills the widget."""
        # Get actual widget size
        try:
            widget_width = self.winfo_width()
            widget_height = self.winfo_height()
            # If widget hasn't been sized yet, use defaults
            if widget_width <= 1:
                widget_width = self.button_width if self.button_width else 200
            if widget_height <= 1:
                widget_height = self.button_height
        except:
            # Fallback to calculated dimensions
            if self.button_width:
                widget_width = self.button_width
            else:
                widget_width = len(self.button_text) * 9 + 60
            widget_height = self.button_height
        
        # Use full widget size (fill the container)
        width = max(widget_width, 100)
        height = max(widget_height, 40)
        
        # Create base image with transparent background
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Main button rectangle - fill entire image
        button_rect = [0, 0, width, height]
        
        # Background color with subtle gradient
        bg_rgb = self._hex_to_rgb(bg_color)
        draw.rounded_rectangle(button_rect, radius=self.radius, fill=(*bg_rgb, 255))
        
        # Subtle inner highlight (top edge)
        highlight_rect = [0, 0, width, 2]
        highlight_rgb = tuple(min(255, c + 15) for c in bg_rgb)
        draw.rounded_rectangle(highlight_rect, radius=self.radius, fill=(*highlight_rgb, 100))
        
        # Add text with glow
        text_img = self._add_text_with_glow(self.button_text, width, height)
        
        # Composite text onto button
        text_x = (width - text_img.width) // 2
        text_y = (height - text_img.height) // 2
        img.paste(text_img, (text_x, text_y), text_img)
        
        # Convert to PhotoImage
        return ImageTk.PhotoImage(img)
    
    def _add_text_with_glow(self, text, width, height):
        """Create text image with glow effect."""
        # Create larger temporary image for glow effect
        padding = 20  # Extra space for glow
        temp_img = Image.new('RGBA', (width + padding * 2, height + padding * 2), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # Font size
        font_size = self.button_font[1]
        font = None
        
        # Try different font paths
        font_paths = [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",  # Bold version
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",  # Bold version
        ]
        
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        
        if font is None:
            try:
                font = ImageFont.load_default()
            except:
                font = None
        
        if font is None:
            # Fallback: just return empty image
            return temp_img
        
        # Get text dimensions
        try:
            bbox = temp_draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            # Fallback if textbbox fails
            text_width = len(text) * font_size // 2
            text_height = font_size
        
        # Calculate position (centered)
        x = (width + padding * 2 - text_width) // 2
        y = (height + padding * 2 - text_height) // 2
        
        text_rgb = self._hex_to_rgb(self.text_color)
        
        # Draw glow layers (multiple layers with increasing blur effect)
        glow_intensity = 5
        for i in range(glow_intensity, 0, -1):
            # Create glow layer with reduced opacity
            alpha = int(30 * (i / glow_intensity))
            glow_color = (*text_rgb, alpha)
            
            # Draw multiple offset copies for glow effect
            offsets = [
                (x - i, y - i), (x, y - i), (x + i, y - i),
                (x - i, y), (x + i, y),
                (x - i, y + i), (x, y + i), (x + i, y + i)
            ]
            for offset_x, offset_y in offsets:
                temp_draw.text((offset_x, offset_y), text, font=font, fill=glow_color)
        
        # Draw main text (white, full opacity)
        temp_draw.text((x, y), text, font=font, fill=(*text_rgb, 255))
        
        return temp_img
    
    def on_enter(self, e):
        """Handle mouse enter - show hover state."""
        self.config(image=self.hover_image)
    
    def on_leave(self, e):
        """Handle mouse leave - show default state."""
        self.config(image=self.default_image)
    
    def on_press(self, e):
        """Handle mouse press - show active state."""
        self.config(image=self.active_image)
    
    def on_release(self, e):
        """Handle mouse release - show hover state."""
        self.config(image=self.hover_image)
    
    def _lighten_color(self, color, amount=20):
        """Lighten a hex color by specified amount."""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(min(255, c + amount) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


class CustomDropdown(tk.Frame):
    """Simple curved dropdown with rounded corners."""
    def __init__(self, parent, values, **kwargs):
        super().__init__(parent)
        
        self.values = values
        self.textvariable = kwargs.get('textvariable', None)
        if self.textvariable:
            initial_value = self.textvariable.get()
            if initial_value and initial_value in values:
                self.selected_value = self.textvariable
            else:
                self.selected_value = tk.StringVar(value=values[0] if values else "")
                if self.textvariable:
                    self.textvariable.set(values[0] if values else "")
        else:
            self.selected_value = tk.StringVar(value=values[0] if values else "")
        
        self.callback = kwargs.get('command', None)
        self.width = kwargs.get('width', 150)
        self.font = kwargs.get('font', ("Segoe UI", 12))
        
        # Colors
        self.bg_color = "#2a2f3b"
        self.hover_color = "#323741"
        self.text_color = "#ffffff"
        self.radius = 8
        
        # State
        self.is_open = False
        self.current_index = 0
        
        # Create main container
        self.configure(bg=COLORS["bg_primary"])
        
        # Create rounded frame using canvas for curved corners
        self.canvas = tk.Canvas(
            self,
            bg=COLORS["bg_primary"],
            highlightthickness=0,
            borderwidth=0,
            width=self.width,
            height=35
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw rounded rectangle background
        self._draw_rounded_frame()
        
        # Selected text label
        initial_text = self.selected_value.get() if self.selected_value else (self.values[0] if self.values else "")
        self.selected_label = tk.Label(
            self.canvas,
            text=initial_text,
            bg=self.bg_color,
            fg=self.text_color,
            font=self.font,
            anchor="w",
            padx=10,
            pady=8
        )
        self.canvas.create_window(5, 17, window=self.selected_label, anchor="w", width=self.width - 30)
        
        # Arrow icon
        self.arrow_label = tk.Label(
            self.canvas,
            text="▼",
            bg=self.bg_color,
            fg=self.text_color,
            font=("Segoe UI", 10),
            padx=5
        )
        self.canvas.create_window(self.width - 15, 17, window=self.arrow_label, anchor="e")
        
        # Update canvas on resize
        self.canvas.bind("<Configure>", lambda e: self._draw_rounded_frame())
        
        # Options listbox (initially hidden)
        self.options_listbox = tk.Listbox(
            self,
            bg=self.bg_color,
            fg=self.text_color,
            font=self.font,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            selectbackground=self.hover_color,
            selectforeground=self.text_color,
            activestyle='none'
        )
        
        # Add values to listbox
        for value in self.values:
            self.options_listbox.insert(tk.END, value)
        
        # Bind events
        self.canvas.bind("<Button-1>", self._on_click)
        self.selected_label.bind("<Button-1>", self._on_click)
        self.arrow_label.bind("<Button-1>", self._on_click)
        self.options_listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
        
        # Trace StringVar changes if provided
        if self.textvariable:
            self.textvariable.trace('w', self._on_var_change)
    
    def _draw_rounded_frame(self):
        """Draw rounded rectangle on canvas."""
        self.canvas.delete("rounded_bg")
        # Draw rounded rectangle (simulated with multiple rectangles)
        self.canvas.create_rectangle(
            0, self.radius, self.width, 35 - self.radius,
            fill=self.bg_color, outline="", tags="rounded_bg"
        )
        self.canvas.create_oval(
            0, 0, self.radius * 2, self.radius * 2,
            fill=self.bg_color, outline="", tags="rounded_bg"
        )
        self.canvas.create_oval(
            self.width - self.radius * 2, 0, self.width, self.radius * 2,
            fill=self.bg_color, outline="", tags="rounded_bg"
        )
        self.canvas.create_oval(
            0, 35 - self.radius * 2, self.radius * 2, 35,
            fill=self.bg_color, outline="", tags="rounded_bg"
        )
        self.canvas.create_oval(
            self.width - self.radius * 2, 35 - self.radius * 2, self.width, 35,
            fill=self.bg_color, outline="", tags="rounded_bg"
        )
    
    def _on_click(self, e):
        """Toggle dropdown on click."""
        if self.is_open:
            self._close_dropdown()
        else:
            self._open_dropdown()
    
    def _open_dropdown(self):
        """Open the dropdown."""
        self.is_open = True
        self.arrow_label.config(text="▲")
        # Show listbox below canvas
        self.options_listbox.pack(fill=tk.X, pady=(3, 0))
        self.options_listbox.config(height=min(len(self.values), 5))  # Show max 5 items
        self.update_idletasks()
    
    def _close_dropdown(self):
        """Close the dropdown."""
        self.is_open = False
        self.arrow_label.config(text="▼")
        self.options_listbox.pack_forget()
    
    def _on_listbox_select(self, e):
        """Handle listbox selection."""
        selection = self.options_listbox.curselection()
        if selection:
            index = selection[0]
            value = self.values[index]
            self.current_index = index
            
            if self.textvariable:
                self.textvariable.set(value)
            else:
                self.selected_value.set(value)
            
            self.selected_label.config(text=value)
            self._close_dropdown()
            
            if self.callback:
                self.callback(value)
    
    def _on_var_change(self, *args):
        """Handle StringVar changes from outside."""
        if self.textvariable:
            value = self.textvariable.get()
            if value in self.values:
                self.selected_label.config(text=value)
                if not self.textvariable == self.selected_value:
                    self.selected_value.set(value)
    
    def get(self):
        """Get current selected value."""
        return self.selected_value.get()
    
    def set(self, value):
        """Set selected value."""
        if value in self.values:
            self.selected_value.set(value)
            self.selected_label.config(text=value)
            if self.textvariable:
                self.textvariable.set(value)
    
    def config(self, **kwargs):
        """Configure dropdown options."""
        if 'command' in kwargs:
            self.callback = kwargs['command']
        if 'width' in kwargs:
            self.width = kwargs['width']
            self.canvas.config(width=self.width)
            self._draw_rounded_frame()
        if 'font' in kwargs:
            self.font = kwargs['font']
            self.selected_label.config(font=self.font)
            self.options_listbox.config(font=self.font)


class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition System")
        self.root.geometry("1200x800")
        self.root.configure(bg=COLORS["bg_primary"])
        
        # Center window on screen
        self.center_window()
        
        # Variables
        self.current_person_name = tk.StringVar()
        self.model_type = tk.StringVar(value="hog")  # For face_recognition encoding model
        self.detection_model = tk.StringVar(value=DEFAULT_MODEL)  # Face detection model
        self.camera_index = tk.IntVar(value=0)
        self.camera_running = False
        self.video_capture = None
        self.video_processing = False
        self.camera_flip_horizontal = tk.BooleanVar(value=False)
        self.camera_flip_vertical = tk.BooleanVar(value=False)
        self.camera_rotate = tk.IntVar(value=0)  # 0, 90, 180, 270 degrees
        
        # Gemini Live API
        self.gemini_api_key = tk.StringVar(value="")
        self.gemini_live_api: Optional[GeminiLiveAPI] = None
        self.live_api_enabled = False
        self.load_gemini_api_key()
        
        # Model-specific data
        self.loaded_encodings = {}  # Dict: {model_name: encodings}
        self.processed_files = {}  # Dict: {model_name: set of files}
        self.detectors = {}  # Cache detectors
        
        # DeepFace calibration
        self.deepface_calibrator = None
        try:
            self.deepface_calibrator = DeepFaceCalibrator()
        except Exception as e:
            print(f"Warning: Could not initialize DeepFace calibrator: {e}")
        
        # Smart Attendance tracking
        self.seen_today = set()  # Track students marked present today
        self.attendance_date = None  # Track the date for automatic reset
        
        # Load encodings for all models
        self.load_all_encodings()
        self.load_all_processed_files()
        
        # Create UI
        self.create_homepage()
    
    def setup_modern_styles(self):
        """Configure modern ttk styles for dropdowns and widgets."""
        style = ttk.Style()
        style.theme_use('clam')  # Use clam as base theme
        
        # Modern Combobox style
        style.configure('Modern.TCombobox',
            fieldbackground=COLORS['bg_tertiary'],
            background=COLORS['bg_tertiary'],
            foreground=COLORS['text_primary'],
            borderwidth=0,
            relief=tk.FLAT,
            padding=10,
            arrowcolor=COLORS['text_secondary'],
            selectbackground=COLORS['accent_blue'],
            selectforeground=COLORS['text_primary']
        )
        style.map('Modern.TCombobox',
            fieldbackground=[('readonly', COLORS['bg_tertiary'])],
            background=[('readonly', COLORS['bg_tertiary'])],
            foreground=[('readonly', COLORS['text_primary'])],
            bordercolor=[('focus', COLORS['accent_blue'])],
            lightcolor=[('focus', COLORS['accent_blue'])],
            darkcolor=[('focus', COLORS['accent_blue'])]
        )
        
        # Modern Entry style
        style.configure('Modern.TEntry',
            fieldbackground=COLORS['bg_tertiary'],
            foreground=COLORS['text_primary'],
            borderwidth=1,
            relief=tk.FLAT,
            padding=8,
            bordercolor=COLORS['border'],
            lightcolor=COLORS['border'],
            darkcolor=COLORS['border']
        )
        style.map('Modern.TEntry',
            bordercolor=[('focus', COLORS['accent_blue'])],
            lightcolor=[('focus', COLORS['accent_blue'])],
            darkcolor=[('focus', COLORS['accent_blue'])]
        )
    
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def load_all_encodings(self):
        """Load face encodings for all models."""
        for model_name, encodings_path in ENCODINGS_PATHS.items():
            try:
                if encodings_path.exists():
                    with encodings_path.open(mode="rb") as f:
                        self.loaded_encodings[model_name] = pickle.load(f)
                else:
                    self.loaded_encodings[model_name] = None
            except Exception as e:
                print(f"Error loading encodings for {model_name}: {e}")
                self.loaded_encodings[model_name] = None
    
    def load_all_processed_files(self):
        """Load processed files for all models."""
        for model_name, processed_path in PROCESSED_FILES_PATHS.items():
            try:
                if processed_path.exists():
                    with processed_path.open(mode="rb") as f:
                        self.processed_files[model_name] = pickle.load(f)
                else:
                    self.processed_files[model_name] = set()
            except Exception as e:
                print(f"Error loading processed files for {model_name}: {e}")
                self.processed_files[model_name] = set()
    
    def save_processed_files(self, model_name=None):
        """Save list of processed files for a specific model."""
        if model_name is None:
            model_name = self.detection_model.get()
        
        try:
            processed_path = PROCESSED_FILES_PATHS[model_name]
            with processed_path.open(mode="wb") as f:
                pickle.dump(self.processed_files.get(model_name, set()), f)
        except Exception as e:
            print(f"Error saving processed files for {model_name}: {e}")
    
    def get_current_encodings(self):
        """Get encodings for current detection model."""
        model_name = self.detection_model.get()
        return self.loaded_encodings.get(model_name)
    
    def get_current_processed_files(self):
        """Get processed files for current detection model."""
        model_name = self.detection_model.get()
        return self.processed_files.get(model_name, set())
    
    def get_detector(self):
        """Get detector for current model. Only loads the selected model."""
        model_name = self.detection_model.get()
        
        # Only load the selected model (unloading is handled in on_model_change)
        if model_name not in self.detectors:
            if model_name == "yolov8":
                self.detectors[model_name] = YOLOv8FaceDetector()
            elif model_name == "yolov11":
                self.detectors[model_name] = YOLOFaceDetector()
            elif model_name == "retinaface":
                try:
                    self.detectors[model_name] = RetinaFaceDetector()
                except ImportError:
                    raise ImportError(
                        "RetinaFace is not installed. Please install it with: pip install retina-face"
                    )
            elif model_name == "deepface":
                try:
                    self.detectors[model_name] = DeepFaceDetector()
                except ImportError:
                    raise ImportError(
                        "DeepFace is not installed. Please install it with: pip install deepface"
                    )
        
        return self.detectors[model_name]
    
    def clear_frame(self):
        """Clear all widgets from the main frame."""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def create_homepage(self):
        """Create the main homepage with modern dark theme."""
        self.clear_frame()
        
        # Header with gradient effect
        header_frame = tk.Frame(self.root, bg=COLORS["bg_secondary"], height=120)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Title with icon
        title_container = tk.Frame(header_frame, bg=COLORS["bg_secondary"])
        title_container.pack(expand=True, fill=tk.BOTH, pady=20)
        
        title_label = tk.Label(
            title_container,
            text="Face Recognition System",
            font=("Segoe UI", 36, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        )
        title_label.pack()
        
        # Main content frame
        content_frame = tk.Frame(self.root, bg=COLORS["bg_primary"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        # Model Selection Card
        model_card = tk.Frame(
            content_frame,
            bg=COLORS["bg_secondary"],
            relief=tk.FLAT,
            bd=0
        )
        model_card.pack(fill=tk.X, pady=(0, 20))
        
        model_header = tk.Frame(model_card, bg=COLORS["bg_secondary"])
        model_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        tk.Label(
            model_header,
            text="Detection Model",
            font=("Segoe UI", 13, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(side=tk.LEFT, padx=(0, 12))
        
        # Check if RetinaFace is available
        retinaface_available = False
        try:
            import retinaface
            retinaface_available = True
        except:
            pass
        
        # Check if DeepFace is available
        deepface_available = False
        try:
            import deepface
            deepface_available = True
        except:
            pass
        
        model_options_home = ["yolov11", "yolov8"]
        if retinaface_available:
            model_options_home.append("retinaface")
        if deepface_available:
            model_options_home.append("deepface")
        
        model_combo_home = ttk.Combobox(
            model_header,
            values=model_options_home,
            textvariable=self.detection_model,
            width=18,
            state="readonly"
        )
        model_combo_home.pack(side=tk.LEFT, padx=8, pady=3)
        model_combo_home.bind("<<ComboboxSelected>>", lambda e: self._on_model_change_home())
        
        # Model description
        model_desc_home = tk.Label(
            model_header,
            text="",
            font=("Segoe UI", 10),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_tertiary"]
        )
        model_desc_home.pack(side=tk.LEFT, padx=12)
        
        def update_home_model_desc(*args):
            model_name = self.detection_model.get()
            desc_map = {
                "yolov11": "Latest YOLO, best accuracy",
                "yolov8": "Stable YOLO version",
                "retinaface": "Deep learning with landmarks",
                "deepface": "Face recognition + Emotion/Age/Race/Gender"
            }
            model_desc_home.config(text=desc_map.get(model_name, ""))
            # Unload other models
            self.root.after_idle(lambda: self._unload_other_models(model_name))
            # Update status
            self.root.after(100, lambda: self._update_homepage_status())
        
        self.detection_model.trace('w', update_home_model_desc)
        update_home_model_desc()
        
        # Status card with modern design
        status_card = tk.Frame(
            content_frame,
            bg=COLORS["bg_secondary"],
            relief=tk.FLAT,
            bd=0
        )
        status_card.pack(fill=tk.X, pady=(0, 30))
        
        # Status header
        status_header = tk.Frame(status_card, bg=COLORS["bg_secondary"])
        status_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        tk.Label(
            status_header,
            text="System Status",
            font=("Segoe UI", 15, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(side=tk.LEFT)
        
        # Status indicator (will be updated dynamically)
        status_body = tk.Frame(status_card, bg=COLORS["bg_secondary"])
        status_body.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.status_label = tk.Label(
            status_body,
            text="",
            font=("Segoe UI", 11),
            bg=COLORS["bg_secondary"],
            fg=COLORS["success"],
            anchor="w"
        )
        self.status_label.pack(fill=tk.X)
        
        # Initial status update
        self._update_homepage_status()
        
        # Buttons grid with modern cards
        buttons_container = tk.Frame(content_frame, bg=COLORS["bg_primary"])
        buttons_container.pack(fill=tk.BOTH, expand=True)
        
        # Create button cards
        buttons = [
            {
                "text": "Train Model",
                "command": self.show_training_page,
                "color": COLORS["bg_tertiary"],
                "desc": "Add people and train recognition"
            },
            {
                "text": "Live Recognition",
                "command": self.start_live_recognition,
                "color": COLORS["bg_tertiary"],
                "desc": "Real-time camera recognition"
            },
            {
                "text": "Test Image",
                "command": self.test_image,
                "color": COLORS["bg_tertiary"],
                "desc": "Test on uploaded images"
            },
            {
                "text": "DeepFace Calibration",
                "command": self.show_deepface_calibration_page,
                "color": COLORS["bg_tertiary"],
                "desc": "Improve emotion, age, race accuracy"
            },
            {
                "text": "View People",
                "command": self.view_registered_people,
                "color": COLORS["bg_tertiary"],
                "desc": "Browse registered people"
            },
            {
                "text": "Settings",
                "command": self.show_settings,
                "color": COLORS["bg_tertiary"],
                "desc": "Configure system settings"
            },
            {
                "text": "Smart Attendance",
                "command": self.start_smart_attendance,
                "color": COLORS["bg_tertiary"],
                "desc": "Mark attendance in Google Sheet"
            },
        ]
        
        # Create button grid
        for i, btn_info in enumerate(buttons):
            row = i // 2
            col = i % 2
            
            # Card frame
            card = tk.Frame(
                buttons_container,
                bg=COLORS["bg_secondary"],
                relief=tk.FLAT,
                bd=0
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)
            
            # Button
            btn = tk.Button(
                card,
                text=btn_info["text"],
                bg=btn_info["color"],
                fg=COLORS["text_primary"],
                command=btn_info["command"],
                font=("Segoe UI", 13, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                padx=20,
                pady=12
            )
            btn.pack(fill=tk.X, padx=24, pady=(24, 12))
            
            # Description
            desc_label = tk.Label(
                card,
                text=btn_info["desc"],
                font=("Segoe UI", 10),
                bg=COLORS["bg_secondary"],
                fg=COLORS["text_tertiary"]
            )
            desc_label.pack(pady=(0, 24))
        
        # Configure grid weights
        buttons_container.grid_columnconfigure(0, weight=1)
        buttons_container.grid_columnconfigure(1, weight=1)
        buttons_container.grid_rowconfigure(0, weight=1)
        buttons_container.grid_rowconfigure(1, weight=1)
        buttons_container.grid_rowconfigure(2, weight=1)
        buttons_container.grid_rowconfigure(3, weight=1)
    
    def show_training_page(self):
        """Show the training page with modern dark theme."""
        self.clear_frame()
        
        # Header
        header_frame = tk.Frame(self.root, bg=COLORS["bg_secondary"], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        back_btn = tk.Button(
            header_frame,
            text="← Home",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            command=self.create_homepage,
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=18,
            pady=10
        )
        back_btn.pack(side=tk.LEFT, padx=24, pady=20)
        
        title_label = tk.Label(
            header_frame,
            text="Train Model",
            font=("Segoe UI", 28, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        )
        title_label.pack(side=tk.LEFT, padx=24, pady=20)
        
        # Main content
        content_frame = tk.Frame(self.root, bg=COLORS["bg_primary"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        # Left panel - Add Person
        left_card = tk.Frame(
            content_frame,
            bg=COLORS["bg_secondary"],
            relief=tk.FLAT
        )
        left_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(
            left_card,
            text="Add New Person",
            font=("Segoe UI", 18, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(pady=(28, 20))
        
        tk.Label(
            left_card,
            text="Person Name",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(anchor=tk.W, padx=24, pady=(14, 8))
        
        name_entry = tk.Entry(
            left_card,
            textvariable=self.current_person_name,
            font=("Segoe UI", 11),
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent_blue"]
        )
        name_entry.pack(fill=tk.X, padx=20, pady=5, ipady=8)
        
        # Buttons frame
        buttons_frame = tk.Frame(left_card, bg=COLORS["bg_secondary"])
        buttons_frame.pack(pady=20)
        
        add_photos_btn = tk.Button(
            buttons_frame,
            text="Add Photos",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            command=lambda: self.add_photos_for_person(self.current_person_name.get()),
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=12
        )
        add_photos_btn.pack(pady=6)
        
        add_video_btn = tk.Button(
            buttons_frame,
            text="Add Video",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            command=lambda: self.add_video_for_person(self.current_person_name.get()),
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=12
        )
        add_video_btn.pack(pady=6)
        
        import_folder_btn = tk.Button(
            buttons_frame,
            text="Import Folder",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            command=self.import_from_folder,
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=12
        )
        import_folder_btn.pack(pady=6)
        
        # Right panel - Training
        right_card = tk.Frame(
            content_frame,
            bg=COLORS["bg_secondary"],
            relief=tk.FLAT
        )
        right_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(
            right_card,
            text="Training Configuration",
            font=("Segoe UI", 18, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(pady=(28, 20))
        
        # Face Detection Model Selection
        tk.Label(
            right_card,
            text="Face Detection Model",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(anchor=tk.W, padx=24, pady=(14, 6))
        
        model_desc = tk.Label(
            right_card,
            text="Each model has separate training data",
            font=("Segoe UI", 10),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_tertiary"]
        )
        model_desc.pack(anchor=tk.W, padx=24, pady=(0, 12))
        
        model_dropdown_frame = tk.Frame(right_card, bg=COLORS["bg_secondary"])
        model_dropdown_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Check if RetinaFace is available (lazy check - don't load model)
        retinaface_available = False
        retinaface_error = None
        try:
            # Just check if module can be imported, don't create detector
            import retinaface
            retinaface_available = True
        except ImportError as e:
            retinaface_available = False
            retinaface_error = str(e)
        except Exception as e:
            retinaface_available = False
            retinaface_error = f"{type(e).__name__}: {str(e)}"
        
        # Check if DeepFace is available
        deepface_available = False
        deepface_error = None
        try:
            import deepface
            deepface_available = True
        except ImportError as e:
            deepface_available = False
            deepface_error = str(e)
        except Exception as e:
            deepface_available = False
            deepface_error = f"{type(e).__name__}: {str(e)}"
        
        model_options = [
            ("YOLOv11", "yolov11", "Latest YOLO, best accuracy"),
            ("YOLOv8", "yolov8", "Stable YOLO version"),
        ]
        
        if retinaface_available:
            model_options.append(("RetinaFace", "retinaface", "Deep learning with landmarks"))
        else:
            # Show specific error if available
            if retinaface_error and "tf-keras" in retinaface_error.lower():
                model_options.append(("RetinaFace (Needs tf-keras)", "retinaface", "Install: pip install tf-keras"))
            else:
                model_options.append(("RetinaFace (Not Available)", "retinaface", "Check dependencies"))
        
        if deepface_available:
            model_options.append(("DeepFace", "deepface", "Face recognition + Emotion/Age/Race/Gender"))
        else:
            model_options.append(("DeepFace (Not Installed)", "deepface", "Install: pip install deepface"))
        
        # Model combo for training page
        model_combo = ttk.Combobox(
            model_dropdown_frame,
            values=[opt[1] for opt in model_options],
            textvariable=self.detection_model,
            width=22,
            state="readonly"
        )
        model_combo.pack(side=tk.LEFT, padx=8, pady=3)
        
        # Disable RetinaFace if not available
        if not retinaface_available:
            def check_retinaface_selection(*args):
                if self.detection_model.get() == "retinaface":
                    if retinaface_error and "tf-keras" in retinaface_error.lower():
                        msg = (
                            "RetinaFace requires tf-keras package.\n\n"
                            "Please install it:\n"
                            "pip install tf-keras\n\n"
                            "Switching to YOLOv11..."
                        )
                    else:
                        msg = (
                            "RetinaFace is not available.\n\n"
                            f"Error: {retinaface_error or 'Unknown error'}\n\n"
                            "Please install dependencies or use YOLOv8/YOLOv11.\n\n"
                            "Switching to YOLOv11..."
                        )
                    messagebox.showwarning("RetinaFace Not Available", msg)
                    self.detection_model.set("yolov11")
            
            # Use trace_add for Python 3.8+ compatibility
            try:
                self.detection_model.trace_add('write', check_retinaface_selection)
            except AttributeError:
                # Fallback for older Python versions
                self.detection_model.trace('w', check_retinaface_selection)
        
        # Model info label
        self.model_info_label = tk.Label(
            model_dropdown_frame,
            text="",
            font=("Segoe UI", 9),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_secondary"]
        )
        self.model_info_label.pack(side=tk.LEFT, padx=10)
        
        def update_model_info(*args):
            model_name = self.detection_model.get()
            for opt in model_options:
                if opt[1] == model_name:
                    self.model_info_label.config(text=opt[2])
                    break
        
        def on_model_change(*args):
            model_name = self.detection_model.get()
            # Unload other models when switching (non-blocking)
            self.root.after_idle(lambda: self._unload_other_models(model_name))
            # Update status (non-blocking)
            self.root.after(100, lambda: self._update_model_status(model_name))
            # Update model info
            update_model_info()
        
        self.detection_model.trace('w', on_model_change)
        update_model_info()  # Initial update
        
        # Encoding Model selection (for face_recognition library)
        tk.Label(
            right_card,
            text="Encoding Model",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(anchor=tk.W, padx=24, pady=(18, 8))
        
        encoding_frame = tk.Frame(right_card, bg=COLORS["bg_secondary"])
        encoding_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Radiobutton(
            encoding_frame,
            text="HOG (CPU - Faster)",
            variable=self.model_type,
            value="hog",
            font=("Segoe UI", 10),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"],
            selectcolor=COLORS["bg_tertiary"],
            activebackground=COLORS["bg_secondary"],
            activeforeground=COLORS["text_primary"]
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Radiobutton(
            encoding_frame,
            text="CNN (GPU - More Accurate)",
            variable=self.model_type,
            value="cnn",
            font=("Segoe UI", 10),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"],
            selectcolor=COLORS["bg_tertiary"],
            activebackground=COLORS["bg_secondary"],
            activeforeground=COLORS["text_primary"]
        ).pack(side=tk.LEFT, padx=10)
        
        # Train button
        train_btn = tk.Button(
            right_card,
            text="Train Model",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            command=self.train_model,
            font=("Segoe UI", 13, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=25,
            pady=15
        )
        train_btn.pack(pady=30)
        
        # Status label
        self.training_status = tk.Label(
            right_card,
            text="",
            font=("Segoe UI", 10),
            bg=COLORS["bg_secondary"],
            fg=COLORS["success"],
            wraplength=300
        )
        self.training_status.pack(pady=10)
        
        # Bottom panel - Registered People
        list_card = tk.Frame(
            content_frame,
            bg=COLORS["bg_secondary"],
            relief=tk.FLAT
        )
        list_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(
            list_card,
            text="Registered People",
            font=("Segoe UI", 18, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(pady=(24, 14))
        
        # Scrollable list
        list_container = tk.Frame(list_card, bg=COLORS["bg_secondary"])
        list_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.people_listbox = tk.Listbox(
            list_container,
            font=("Segoe UI", 11),
            yscrollcommand=scrollbar.set,
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            selectbackground=COLORS["accent_blue"],
            selectforeground=COLORS["text_primary"],
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            activestyle='none'
        )
        self.people_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.people_listbox.yview)
        
        # Initialize people list
        self.update_people_list()
        
        # Delete button
        delete_btn = tk.Button(
            list_card,
            text="Delete Selected",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            command=self.delete_person,
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=12
        )
        delete_btn.pack(pady=(0, 24))
    
    def show_deepface_calibration_page(self):
        """Show the DeepFace calibration page."""
        if not self.deepface_calibrator:
            messagebox.showerror(
                "DeepFace Not Available",
                "DeepFace calibration requires DeepFace to be installed.\n\n"
                "Install with: pip install deepface"
            )
            return
        
        self.clear_frame()
        
        # Header
        header_frame = tk.Frame(self.root, bg=COLORS["bg_secondary"], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        back_btn = tk.Button(
            header_frame,
            text="← Home",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            command=self.create_homepage,
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=18,
            pady=10
        )
        back_btn.pack(side=tk.LEFT, padx=24, pady=20)
        
        title_label = tk.Label(
            header_frame,
            text="DeepFace Calibration",
            font=("Segoe UI", 28, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        )
        title_label.pack(side=tk.LEFT, padx=24, pady=20)
        
        # Main content
        content_frame = tk.Frame(self.root, bg=COLORS["bg_primary"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        # Info card
        info_card = tk.Frame(
            content_frame,
            bg=COLORS["bg_secondary"],
            relief=tk.FLAT
        )
        info_card.pack(fill=tk.X, pady=(0, 20))
        
        info_text = tk.Text(
            info_card,
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"],
            font=("Segoe UI", 10),
            wrap=tk.WORD,
            height=6,
            relief=tk.FLAT,
            padx=20,
            pady=15
        )
        info_text.pack(fill=tk.BOTH, expand=True)
        info_text.insert("1.0", 
            "📁 Organize your training images in a person folder:\n\n"
            "Create a folder with your name (e.g., 'sreyas/') containing:\n"
            "• emotion/ folder with subfolders: 'happy', 'sad', 'angry', 'surprise', 'fear', 'disgust', 'neutral'\n"
            "• race/ folder with subfolders: 'asian', 'indian', 'black', 'white', 'middle eastern', 'latino'\n"
            "• age/ folder with subfolders named with numbers like '25', '30', '35' (your actual age)\n\n"
            "Example: sreyas/emotion/happy/photo1.jpg\n"
            "Select your person folder below and click 'Train' to improve accuracy!"
        )
        info_text.config(state=tk.DISABLED)
        
        # Person folder selection
        folder_card = tk.Frame(
            content_frame,
            bg=COLORS["bg_secondary"],
            relief=tk.FLAT
        )
        folder_card.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            folder_card,
            text="Person Training Folder",
            font=("Segoe UI", 15, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(anchor=tk.W, padx=24, pady=(18, 6))
        
        tk.Label(
            folder_card,
            text="Select folder containing emotion/, race/, and age/ subfolders (e.g., 'sreyas/')",
            font=("Segoe UI", 10),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_tertiary"]
        ).pack(anchor=tk.W, padx=24, pady=(0, 12))
        
        folder_frame = tk.Frame(folder_card, bg=COLORS["bg_secondary"])
        folder_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.person_folder_path = tk.StringVar(value="")
        folder_entry = tk.Entry(
            folder_frame,
            textvariable=self.person_folder_path,
            font=("Segoe UI", 10),
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            relief=tk.FLAT,
            insertbackground=COLORS["text_primary"]
        )
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        folder_browse_btn = tk.Button(
            folder_frame,
            text="Browse",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            command=lambda: self._browse_folder(self.person_folder_path),
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=5
        )
        folder_browse_btn.pack(side=tk.LEFT)
        
        # Status and Train button
        action_frame = tk.Frame(content_frame, bg=COLORS["bg_primary"])
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.deepface_status = tk.Label(
            action_frame,
            text="Ready to train",
            font=("Segoe UI", 11),
            bg=COLORS["bg_primary"],
            fg=COLORS["text_secondary"]
        )
        self.deepface_status.pack(side=tk.LEFT, padx=(0, 20))
        
        train_btn = tk.Button(
            action_frame,
            text="🚀 Train Calibration",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            command=self.train_deepface_calibration,
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=25,
            pady=12
        )
        train_btn.pack(side=tk.RIGHT)
    
    def _browse_folder(self, path_var):
        """Browse for a folder."""
        folder = filedialog.askdirectory(title="Select Training Folder")
        if folder:
            path_var.set(folder)
    
    def train_deepface_calibration(self):
        """Train DeepFace calibration from selected person folder."""
        if not self.deepface_calibrator:
            messagebox.showerror("Error", "DeepFace calibrator not available")
            return
        
        person_folder_path = self.person_folder_path.get()
        if not person_folder_path:
            messagebox.showwarning(
                "No Folder Selected",
                "Please select a person training folder (e.g., 'sreyas/')."
            )
            return
        
        person_folder = Path(person_folder_path)
        if not person_folder.exists():
            messagebox.showerror(
                "Invalid Folder",
                f"The selected folder does not exist:\n\n{person_folder}"
            )
            return
        
        # Disable train button and show progress
        self.deepface_status.config(text="Training in progress...", fg=COLORS["warning"])
        self.root.update()
        
        def progress_callback(current, total, message):
            self.deepface_status.config(
                text=f"{message} ({current}/{total})",
                fg=COLORS["warning"]
            )
            self.root.update()
        
        try:
            stats = self.deepface_calibrator.train_from_person_folder(
                person_folder=person_folder,
                progress_callback=progress_callback
            )
            
            # Show results
            result_msg = (
                f"Training completed for '{person_folder.name}'!\n\n"
                f"Emotion samples: {stats['emotion_samples']}\n"
                f"Race samples: {stats['race_samples']}\n"
                f"Age samples: {stats['age_samples']}\n"
            )
            
            if stats['errors']:
                result_msg += f"\nWarnings: {len(stats['errors'])}\n"
                if len(stats['errors']) <= 5:
                    result_msg += "\n".join(stats['errors'])
                else:
                    result_msg += "\n".join(stats['errors'][:5]) + f"\n... and {len(stats['errors']) - 5} more"
            
            messagebox.showinfo("Training Complete", result_msg)
            self.deepface_status.config(
                text=f"✓ Trained {person_folder.name}: {stats['emotion_samples']} emotion, {stats['race_samples']} race, {stats['age_samples']} age samples",
                fg=COLORS["success"]
            )
        except Exception as e:
            messagebox.showerror("Training Error", f"Error during training:\n\n{str(e)}")
            self.deepface_status.config(text="Training failed", fg=COLORS["error"])
    
    def _unload_other_models(self, current_model):
        """Unload models that are not currently selected."""
        for other_model in list(self.detectors.keys()):
            if other_model != current_model:
                try:
                    detector = self.detectors[other_model]
                    if hasattr(detector, 'model'):
                        del detector.model
                    del self.detectors[other_model]
                except:
                    pass
        # Keep only current model in cache
        if current_model not in self.detectors:
            self.detectors = {}
        else:
            self.detectors = {current_model: self.detectors[current_model]}
    
    def _update_model_status(self, model_name):
        """Update model status (called asynchronously to avoid lag)."""
        current_encodings = self.get_current_encodings()
        if current_encodings:
            num_people = len(set(current_encodings.get("names", [])))
            self.training_status.config(
                text=f"✓ {model_name.upper()} model selected - {num_people} person(s) trained",
                fg=COLORS["success"]
            )
        else:
            self.training_status.config(
                text=f"⚠ {model_name.upper()} model selected - Not trained yet",
                fg=COLORS["warning"]
            )
    
    def _update_homepage_status(self):
        """Update homepage status label."""
        if hasattr(self, 'status_label'):
            try:
                current_encodings = self.get_current_encodings()
                if current_encodings:
                    num_people = len(set(current_encodings.get("names", [])))
                    model_name = self.detection_model.get().upper()
                    status_text = f"✓ {model_name} Active - {num_people} person(s) registered"
                    status_color = COLORS["success"]
                else:
                    model_name = self.detection_model.get().upper()
                    status_text = f"⚠ {model_name} not trained - Train the model to get started"
                    status_color = COLORS["warning"]
                
                self.status_label.config(text=status_text, fg=status_color)
            except Exception as e:
                # Silently fail if status_label doesn't exist yet
                pass
    
    def add_photos_for_person(self, person_name):
        """Open file dialog to add photos for a person."""
        if not person_name or not person_name.strip():
            messagebox.showerror("Error", "Please enter a person name first!")
            return
        
        person_name = person_name.strip().replace(" ", "_")
        person_dir = TRAINING_DIR / person_name
        person_dir.mkdir(exist_ok=True)
        
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select Photos",
            filetypes=filetypes
        )
        
        if files:
            copied = 0
            for file_path in files:
                try:
                    filename = os.path.basename(file_path)
                    dest_path = person_dir / filename
                    shutil.copy2(file_path, dest_path)
                    copied += 1
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to copy {filename}: {str(e)}")
            
            messagebox.showinfo("Success", f"Added {copied} photo(s) for {person_name}")
            self.update_people_list()
    
    def import_from_folder(self):
        """Import photos from a folder structure where subfolders are person names."""
        folder_path = filedialog.askdirectory(
            title="Select Folder with Person Subfolders",
            mustexist=True
        )
        
        if not folder_path:
            return
        
        folder_path = Path(folder_path)
        
        # Find all subfolders
        subfolders = [f for f in folder_path.iterdir() if f.is_dir()]
        
        if not subfolders:
            messagebox.showwarning(
                "Warning",
                "No subfolders found! Please select a folder containing subfolders named after people."
            )
            return
        
        # Show progress
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Importing Photos")
        progress_window.geometry("500x200")
        progress_window.configure(bg=COLORS["bg_primary"])
        
        progress_label = tk.Label(
            progress_window,
            text=f"Scanning {len(subfolders)} folder(s)...",
            font=("Segoe UI", 11),
            bg=COLORS["bg_primary"],
            fg=COLORS["text_primary"]
        )
        progress_label.pack(pady=30)
        
        def import_thread():
            try:
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.JPG', '.JPEG', '.PNG', '.BMP'}
                total_copied = 0
                people_imported = []
                
                for subfolder in subfolders:
                    person_name = subfolder.name.strip().replace(" ", "_")
                    person_dir = TRAINING_DIR / person_name
                    person_dir.mkdir(exist_ok=True)
                    
                    # Find all image files in subfolder
                    image_files = [f for f in subfolder.iterdir() 
                                 if f.is_file() and f.suffix in image_extensions]
                    
                    if not image_files:
                        continue
                    
                    copied = 0
                    for image_file in image_files:
                        try:
                            # Copy to training directory
                            dest_path = person_dir / image_file.name
                            # If file exists, add timestamp to avoid overwrite
                            if dest_path.exists():
                                stem = dest_path.stem
                                suffix = dest_path.suffix
                                dest_path = person_dir / f"{stem}_imported{suffix}"
                            
                            shutil.copy2(image_file, dest_path)
                            copied += 1
                            total_copied += 1
                        except Exception as e:
                            print(f"Error copying {image_file}: {e}")
                    
                    if copied > 0:
                        people_imported.append(f"{person_name} ({copied} photos)")
                
                progress_window.destroy()
                
                if total_copied > 0:
                    msg = f"Successfully imported {total_copied} photo(s) from {len(people_imported)} person(s):\n\n"
                    msg += "\n".join(people_imported)
                    messagebox.showinfo("Import Complete", msg)
                    self.update_people_list()
                else:
                    messagebox.showwarning("Warning", "No image files found in subfolders!")
                    
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("Error", f"Failed to import folder: {str(e)}")
        
        threading.Thread(target=import_thread, daemon=True).start()
    
    def update_people_list(self):
        """Update the list of registered people."""
        if not hasattr(self, 'people_listbox'):
            return  # People listbox not created yet
        self.people_listbox.delete(0, tk.END)
        if TRAINING_DIR.exists():
            for person_dir in TRAINING_DIR.iterdir():
                if person_dir.is_dir():
                    num_photos = len(list(person_dir.glob("*")))
                    self.people_listbox.insert(
                        tk.END,
                        f"{person_dir.name} ({num_photos} photos)"
                    )
    
    def delete_person(self):
        """Delete selected person and their photos."""
        if not hasattr(self, 'people_listbox'):
            messagebox.showwarning("Warning", "Please go to Training page first!")
            return
        selection = self.people_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a person to delete!")
            return
        
        person_name = self.people_listbox.get(selection[0]).split(" (")[0]
        
        if messagebox.askyesno("Confirm", f"Delete {person_name} and all their photos?"):
            person_dir = TRAINING_DIR / person_name
            if person_dir.exists():
                shutil.rmtree(person_dir)
                messagebox.showinfo("Success", f"Deleted {person_name}")
                self.update_people_list()
    
    def convert_image_to_rgb(self, image_path):
        """Convert image to RGB format."""
        pil_image = Image.open(image_path)
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        return np.array(pil_image, dtype=np.uint8)
    
    def train_model(self, incremental=True):
        """Train the face recognition model with incremental support."""
        if not any(TRAINING_DIR.iterdir()):
            messagebox.showerror("Error", "No training data found! Please add people and photos first.")
            return
        
        # Check if selected model is available
        model_name = self.detection_model.get()
        if model_name == "retinaface":
            try:
                # Just verify import, don't create detector yet
                import retinaface
            except ImportError as e:
                error_msg = str(e)
                if "tf-keras" in error_msg.lower():
                    messagebox.showerror(
                        "RetinaFace Missing Dependency",
                        "RetinaFace requires tf-keras package.\n\n"
                        "Please install it:\n"
                        "pip install tf-keras\n\n"
                        "Or use YOLOv8 or YOLOv11 instead."
                    )
                else:
                    messagebox.showerror(
                        "RetinaFace Not Installed",
                        "RetinaFace package is not installed.\n\n"
                        "Please install it first:\n"
                        "pip install retina-face\n\n"
                        "Or select a different model (YOLOv8 or YOLOv11)."
                    )
                return
            except Exception as e:
                messagebox.showerror(
                    "RetinaFace Error",
                    f"RetinaFace cannot be used:\n\n{str(e)}\n\n"
                    "Please use YOLOv8 or YOLOv11 instead."
                )
                return
        elif model_name == "deepface":
            try:
                # Just verify import, don't create detector yet
                import deepface
            except ImportError as e:
                messagebox.showerror(
                    "DeepFace Not Installed",
                    "DeepFace package is not installed.\n\n"
                    "Please install it first:\n"
                    "pip install deepface\n\n"
                    "Or select a different model (YOLOv8, YOLOv11, or RetinaFace)."
                )
                return
            except Exception as e:
                messagebox.showerror(
                    "DeepFace Error",
                    f"DeepFace cannot be used:\n\n{str(e)}\n\n"
                    "Please use YOLOv8, YOLOv11, or RetinaFace instead."
                )
                return
        
        # Get encoding model info for status
        encoding_model_type = self.model_type.get()
        encoding_model_name = "Small (HOG)" if encoding_model_type == "hog" else "Large (CNN)"
        self.training_status.config(
            text=f"Training in progress... Using {encoding_model_name} encoding model. Please wait.", 
            fg=COLORS["warning"]
        )
        self.root.update_idletasks()  # Use update_idletasks instead of update for better performance
        
        def train_thread():
            try:
                # Get current model name and encoding model type
                model_name = self.detection_model.get()
                encoding_model_type = self.model_type.get()  # "hog" or "cnn"
                # Map to face_recognition encoding model: HOG -> small (faster), CNN -> large (more accurate)
                encoding_model = "small" if encoding_model_type == "hog" else "large"
                
                # Get detector early to catch any errors
                try:
                    detector = self.get_detector()
                except Exception as e:
                    self.root.after(0, lambda err=str(e): messagebox.showerror(
                        "Detector Error",
                        f"Failed to load {model_name} detector:\n\n{err}\n\nPlease try a different model."
                    ))
                    self.root.after(0, lambda: self.training_status.config(
                        text="Training failed - Detector error",
                        fg=COLORS["error"]
                    ))
                    return
                
                current_encodings = self.get_current_encodings()
                
                # Load existing encodings for incremental training
                existing_names = []
                existing_encodings = []
                if incremental and current_encodings:
                    existing_names = current_encodings.get("names", [])
                    existing_encodings = current_encodings.get("encodings", [])
                
                names = list(existing_names) if incremental else []
                encodings = list(existing_encodings) if incremental else []
                processed_count = 0
                new_count = 0
                skipped_count = 0
                error_count = 0
                error_files = []
                
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.JPG', '.JPEG', '.PNG', '.BMP'}
                video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.MP4', '.AVI', '.MOV', '.MKV'}
                all_files = list(TRAINING_DIR.glob("*/*"))
                
                # Filter files to process
                files_to_process = []
                for f in all_files:
                    if f.is_file() and (f.suffix in image_extensions or f.suffix in video_extensions):
                        # For incremental training, check if file is new or modified
                        file_key = str(f.relative_to(TRAINING_DIR))
                        processed_files_set = self.get_current_processed_files()
                        if incremental and file_key in processed_files_set:
                            # Check if file was modified
                            try:
                                if f.exists():
                                    current_mtime = f.stat().st_mtime
                                    # If file was modified, reprocess it
                                    if file_key not in self.processed_files or True:  # Always check
                                        files_to_process.append((f, file_key))
                                    else:
                                        skipped_count += 1
                                else:
                                    skipped_count += 1
                            except:
                                files_to_process.append((f, file_key))
                        else:
                            files_to_process.append((f, file_key))
                
                total_files = len(files_to_process)
                
                if total_files == 0:
                    if incremental and len(names) > 0:
                        # All files already processed
                        self.root.after(0, lambda: messagebox.showinfo(
                            "Info",
                            "All files are already trained! No new files to process."
                        ))
                        self.root.after(0, lambda: self.training_status.config(
                            text=f"✓ All files trained ({len(set(names))} person(s))",
                            fg=COLORS["success"]
                        ))
                    else:
                        self.root.after(0, lambda: messagebox.showerror(
                            "Error",
                            "No image files found in training directory! Please add photos first."
                        ))
                        self.root.after(0, lambda: self.training_status.config(text="", fg=COLORS["success"]))
                    return
                
                for filepath, file_key in files_to_process:
                    name = filepath.parent.name
                    try:
                        if filepath.suffix.lower() in [ext.lower() for ext in image_extensions]:
                            # Process image
                            image = self.convert_image_to_rgb(filepath)
                            
                            # Detector already loaded at start of thread
                            face_locations = detector.detect_faces(image)
                            
                            if not face_locations:
                                error_count += 1
                                error_files.append(f"{filepath.name} (no face detected)")
                                continue
                            
                            # Use the encoding model selected by user (HOG -> small, CNN -> large)
                            face_encodings = face_recognition.face_encodings(
                                image, face_locations, model=encoding_model
                            )
                            
                            if not face_encodings:
                                error_count += 1
                                error_files.append(f"{filepath.name} (encoding failed)")
                                continue
                            
                            for encoding in face_encodings:
                                names.append(name)
                                encodings.append(encoding)
                            
                            processed_count += 1
                            new_count += 1
                            # Mark file as processed
                            if model_name not in self.processed_files:
                                self.processed_files[model_name] = set()
                            self.processed_files[model_name].add(file_key)
                        
                        elif filepath.suffix.lower() in [ext.lower() for ext in video_extensions]:
                            # Process video - extract frames
                            # Detector already loaded at start of thread
                            frame_count = 0
                            frames_processed = 0
                            
                            cap = cv2.VideoCapture(str(filepath))
                            if not cap.isOpened():
                                error_count += 1
                                error_files.append(f"{filepath.name} (could not open)")
                                continue
                            
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            frame_interval = max(1, int(fps / 2))  # Extract 2 frames per second
                            
                            while True:
                                ret, frame = cap.read()
                                if not ret:
                                    break
                                
                                if frame_count % frame_interval == 0:
                                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                    
                                    face_locations = detector.detect_faces(rgb_frame)
                                    
                                    if face_locations:
                                        # Use the encoding model selected by user (HOG -> small, CNN -> large)
                                        face_encodings = face_recognition.face_encodings(
                                            rgb_frame, face_locations, model=encoding_model
                                        )
                                        
                                        for encoding in face_encodings:
                                            names.append(name)
                                            encodings.append(encoding)
                                        frames_processed += 1
                                
                                frame_count += 1
                            
                            cap.release()
                            
                            if frames_processed > 0:
                                processed_count += 1
                                new_count += 1
                                # Mark file as processed
                                if model_name not in self.processed_files:
                                    self.processed_files[model_name] = set()
                                self.processed_files[model_name].add(file_key)
                            else:
                                error_count += 1
                                error_files.append(f"{filepath.name} (no faces in video)")
                    
                    except Exception as e:
                        error_count += 1
                        error_files.append(f"{filepath.name}: {str(e)}")
                        print(f"Error processing {filepath}: {e}")
                
                if not names:
                    error_msg = f"No faces found in any training images!\n\n"
                    error_msg += f"Processed: {processed_count} files\n"
                    error_msg += f"Errors: {error_count} files\n\n"
                    if error_files:
                        error_msg += "Problem files:\n" + "\n".join(error_files[:5])
                        if len(error_files) > 5:
                            error_msg += f"\n... and {len(error_files) - 5} more"
                    
                    self.root.after(0, lambda msg=error_msg: messagebox.showerror("Error", msg))
                    self.root.after(0, lambda: self.training_status.config(
                        text="Training failed - No faces found!",
                        fg=COLORS["error"]
                    ))
                    return
                
                name_encodings = {"names": names, "encodings": encodings}
                # Save to model-specific file
                encodings_path = ENCODINGS_PATHS[model_name]
                with encodings_path.open(mode="wb") as f:
                    pickle.dump(name_encodings, f)
                
                # Update loaded encodings
                self.loaded_encodings[model_name] = name_encodings
                
                # Save processed files list
                self.save_processed_files(model_name)
                
                num_people = len(set(names))
                success_msg = f"Model trained successfully!\n\n"
                if incremental and new_count > 0:
                    success_msg += f"✓ {new_count} new file(s) processed\n"
                    if skipped_count > 0:
                        success_msg += f"✓ {skipped_count} file(s) skipped (already trained)\n"
                success_msg += f"✓ {len(names)} total face encoding(s)\n"
                success_msg += f"✓ {num_people} person(s) registered\n"
                success_msg += f"✓ {processed_count} file(s) processed successfully"
                
                if error_count > 0:
                    success_msg += f"\n⚠ {error_count} file(s) had issues"
                
                self.root.after(0, lambda msg=success_msg: messagebox.showinfo("Success", msg))
                encoding_model_name = "Small (HOG)" if encoding_model_type == "hog" else "Large (CNN)"
                self.root.after(0, lambda: self.training_status.config(
                    text=f"✓ Training complete! {num_people} person(s), {len(names)} encoding(s) using {encoding_model_name} model.",
                    fg=COLORS["success"]
                ))
                # Reload encodings for current model
                self.load_all_encodings()
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Training error: {error_details}")
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", 
                    f"Training failed: {str(e)}\n\nCheck console for details."
                ))
                self.root.after(0, lambda: self.training_status.config(
                    text="Training failed!",
                    fg=COLORS["error"]
                ))
        
        threading.Thread(target=train_thread, daemon=True).start()
    
    def recognize_face_in_frame(self, face_encoding):
        """Compare face encoding with known encodings using improved distance-based matching."""
        current_encodings = self.get_current_encodings()
        if not current_encodings:
            return None
        
        # Use face_distance for more accurate matching
        face_distances = face_recognition.face_distance(
            current_encodings["encodings"], face_encoding
        )
        
        # Find the best match (lowest distance)
        best_match_index = np.argmin(face_distances)
        best_distance = face_distances[best_match_index]
        
        # Use a stricter threshold for better accuracy
        # Lower distance = better match (0.0 = identical, 1.0 = very different)
        threshold = 0.40  # Balanced threshold (was 0.35 too strict, 0.45 too loose)
        
        if best_distance <= threshold:
            # Get all matches within threshold and use weighted voting
            matches = face_distances <= threshold
            if matches.sum() > 0:
                # Weight votes by inverse distance (closer = more weight)
                weighted_votes = {}
                for i in range(len(current_encodings["names"])):
                    if matches[i]:
                        name = current_encodings["names"][i]
                        distance = face_distances[i]
                        # Weight: closer faces get higher weight
                        weight = 1.0 / (distance + 0.1)  # Add small value to avoid division by zero
                        if name not in weighted_votes:
                            weighted_votes[name] = 0
                        weighted_votes[name] += weight
                
                if weighted_votes:
                    # Return person with highest weighted vote
                    return max(weighted_votes.items(), key=lambda x: x[1])[0]
        
        return None
    
    def start_live_recognition(self):
        """Start live camera recognition."""
        if not self.get_current_encodings():
            messagebox.showerror(
                "Error", "No trained model found! Please train the model first."
            )
            return
        
        camera_window = tk.Toplevel(self.root)
        camera_window.title("Live Face Recognition")
        camera_window.geometry("1200x800")
        camera_window.resizable(True, True)  # Make window resizable
        camera_window.configure(bg=COLORS["bg_primary"])
        camera_window.minsize(1000, 700)  # Set minimum size
        
        # Main container with horizontal split
        main_container = tk.Frame(camera_window, bg=COLORS["bg_primary"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
        
        # Left side: Video frame
        left_panel = tk.Frame(main_container, bg=COLORS["bg_primary"])
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Video frame
        video_frame = tk.Frame(left_panel, bg=COLORS["bg_secondary"])
        video_frame.pack(fill=tk.BOTH, expand=True)
        
        # Video label
        video_label = tk.Label(video_frame, bg=COLORS["bg_secondary"])
        video_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right side: Live API Status Panel
        right_panel = tk.Frame(main_container, bg=COLORS["bg_primary"], width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_panel.pack_propagate(False)
        
        # Live API Status Section
        status_section = tk.Frame(right_panel, bg=COLORS["bg_secondary"], relief=tk.RAISED, bd=2)
        status_section.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        tk.Label(
            status_section,
            text="🎙️ Live Call Status",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Status label
        self.live_api_status_label = tk.Label(
            status_section,
            text="🔴 Disconnected",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["error"],
            anchor=tk.W,
            justify=tk.LEFT
        )
        self.live_api_status_label.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Transcript Section
        transcript_section = tk.Frame(right_panel, bg=COLORS["bg_secondary"], relief=tk.RAISED, bd=2)
        transcript_section.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        tk.Label(
            transcript_section,
            text="💬 Conversation",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Transcript text widget with scrollbar
        transcript_frame = tk.Frame(transcript_section, bg=COLORS["bg_secondary"])
        transcript_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(transcript_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.live_api_transcript_text = tk.Text(
            transcript_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 9),
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
            state=tk.NORMAL,
            height=15
        )
        self.live_api_transcript_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.live_api_transcript_text.yview)
        
        # Initial message
        self.live_api_transcript_text.insert(tk.END, "💡 Start a Live Call to begin conversation...\n", "info")
        self.live_api_transcript_text.tag_config("info", foreground=COLORS["text_secondary"])
        self.live_api_transcript_text.config(state=tk.DISABLED)
        
        # Control frame (bottom section - placed below main_container, not inside it)
        control_frame = tk.Frame(camera_window, bg=COLORS["bg_secondary"])
        control_frame.pack(fill=tk.X, padx=10, pady=(10, 10))
        
        # Top row of controls
        top_controls = tk.Frame(control_frame, bg=COLORS["bg_secondary"])
        top_controls.pack(fill=tk.X, padx=10, pady=10)
        
        # Status label (left side)
        status_label = tk.Label(
            top_controls,
            text="Camera Active - Press 'Stop' to close",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        )
        status_label.pack(side=tk.LEFT, padx=10)
        
        # Camera controls (center)
        camera_controls_frame = tk.Frame(top_controls, bg=COLORS["bg_secondary"])
        camera_controls_frame.pack(side=tk.LEFT, padx=20, expand=True)
        
        # Flip Horizontal button
        flip_h_btn = tk.Button(
            camera_controls_frame,
            text="↔️ Flip H",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["bg_hover"],
            command=lambda: self.camera_flip_horizontal.set(not self.camera_flip_horizontal.get()),
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=6
        )
        flip_h_btn.pack(side=tk.LEFT, padx=5)
        
        # Flip Vertical button
        flip_v_btn = tk.Button(
            camera_controls_frame,
            text="↕️ Flip V",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["bg_hover"],
            command=lambda: self.camera_flip_vertical.set(not self.camera_flip_vertical.get()),
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=6
        )
        flip_v_btn.pack(side=tk.LEFT, padx=5)
        
        # Rotate button (more prominent)
        rotate_btn = tk.Button(
            camera_controls_frame,
            text="🔄 Rotate Camera",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["bg_hover"],
            command=self.rotate_camera,
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        )
        rotate_btn.pack(side=tk.LEFT, padx=5)
        
        # Right side buttons
        right_controls = tk.Frame(top_controls, bg=COLORS["bg_secondary"])
        right_controls.pack(side=tk.RIGHT, padx=10)
        
        # Gemini Live API toggle button (More Prominent)
        self.live_api_toggle_btn = tk.Button(
            right_controls,
            text="🎙️ Live Call: OFF",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["bg_hover"],
            activeforeground=COLORS["text_primary"],
            command=self.toggle_live_api,
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        )
        self.live_api_toggle_btn.pack(side=tk.LEFT, padx=5)
        
        # Stop button
        stop_btn = tk.Button(
            right_controls,
            text="⛔ Stop",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["bg_hover"],
            activeforeground=COLORS["text_primary"],
            command=lambda: self.stop_camera(camera_window),
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        )
        stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.camera_running = True
        self.video_capture = cv2.VideoCapture(self.camera_index.get())
        
        if not self.video_capture.isOpened():
            messagebox.showerror("Error", f"Could not open camera {self.camera_index.get()}")
            camera_window.destroy()
            return
        
        # Performance optimization variables
        process_frame_count = 0
        face_locations_cache = []
        face_names_cache = []
        analysis_cache = {}  # Store analysis for each recognized face
        
        # Audio recording variables
        audio_buffer = []
        last_audio_process_time = 0
        audio_process_interval = 3.0  # Process audio every 3 seconds
        
        def update_frame():
            nonlocal process_frame_count, face_locations_cache, face_names_cache, analysis_cache
            
            if not self.camera_running:
                return
            
            ret, frame = self.video_capture.read()
            if ret:
                # Apply camera transformations (flip/rotate)
                if self.camera_flip_horizontal.get():
                    frame = cv2.flip(frame, 1)  # Horizontal flip
                if self.camera_flip_vertical.get():
                    frame = cv2.flip(frame, 0)  # Vertical flip
                
                # Apply rotation
                rotation = self.camera_rotate.get()
                if rotation == 90:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                elif rotation == 180:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                elif rotation == 270:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                
                # Only process every 3rd frame for better performance
                process_frame_count += 1
                should_process = (process_frame_count % 3 == 0)
                
                if should_process:
                    # Resize for faster processing
                    small_frame = cv2.resize(frame, (0, 0), fx=0.4, fy=0.4)
                    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                    
                    # Detect faces
                    detector = self.get_detector()
                    face_locations_cache = detector.detect_faces(rgb_small_frame)
                    
                    # Get encodings with selected model (HOG -> small, CNN -> large)
                    encoding_model = "small" if self.model_type.get() == "hog" else "large"
                    face_encodings = face_recognition.face_encodings(
                        rgb_small_frame, face_locations_cache, model=encoding_model
                    )
                    
                    # Recognize faces and get analysis
                    face_names_cache = []
                    # Don't reset analysis_cache - keep previous analysis until updated
                    
                    # Get DeepFace analyzer if using DeepFace model
                    deepface_analyzer = None
                    if self.detection_model.get() == "deepface":
                        try:
                            deepface_analyzer = self.get_detector()
                        except:
                            pass
                    
                    for i, face_encoding in enumerate(face_encodings):
                        name = self.recognize_face_in_frame(face_encoding)
                        name = name if name else "Unknown"
                        face_names_cache.append(name)
                        
                        # Get DeepFace analysis for all faces (less frequently for performance)
                        if deepface_analyzer and (process_frame_count % 9 == 0):
                            try:
                                # Scale back to full frame size for analysis
                                scale_factor = 1 / 0.4
                                if i < len(face_locations_cache):
                                    top, right, bottom, left = face_locations_cache[i]
                                    top = int(top * scale_factor)
                                    right = int(right * scale_factor)
                                    bottom = int(bottom * scale_factor)
                                    left = int(left * scale_factor)
                                    
                                    # Extract face region (ensure valid bounds)
                                    top = max(0, top)
                                    left = max(0, left)
                                    bottom = min(frame.shape[0], bottom)
                                    right = min(frame.shape[1], right)
                                    
                                    if bottom > top and right > left:
                                        face_roi = frame[top:bottom, left:right]
                                        if face_roi.size > 0 and face_roi.shape[0] > 20 and face_roi.shape[1] > 20:
                                            import tempfile
                                            import os
                                            temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg')
                                            os.close(temp_fd)
                                            cv2.imwrite(temp_path, face_roi)
                                            
                                            analysis = deepface_analyzer.analyze_face(
                                                temp_path,
                                                actions=['emotion', 'age', 'gender', 'race']
                                            )
                                            
                                            # Store analysis even if partial (some actions may have failed)
                                            # Apply calibration if available
                                            # This combines: 1) DeepFace pre-trained model predictions + 2) Your personal training data
                                            if self.deepface_calibrator and name != "Unknown" and analysis:
                                                try:
                                                    # Apply personal calibration on top of DeepFace model predictions
                                                    analysis = self.deepface_calibrator.calibrate_result(name, analysis)
                                                except Exception as e:
                                                    print(f"Calibration error: {e}")
                                            elif analysis:
                                                # Even without calibration, we still use DeepFace pre-trained model predictions
                                                pass
                                            
                                            # Use face index as key if name is Unknown, otherwise use name
                                            cache_key = name if name != "Unknown" else f"Face_{i}"
                                            analysis_cache[cache_key] = {
                                                'emotion': analysis.get('dominant_emotion', 'N/A') if analysis else 'N/A',
                                                'age': int(analysis.get('age', 0)) if analysis and analysis.get('age') else 0,
                                                'gender': analysis.get('dominant_gender', 'N/A') if analysis else 'N/A',
                                                'race': analysis.get('dominant_race', 'N/A') if analysis else 'N/A'
                                            }
                                            
                                            os.remove(temp_path)
                            except Exception as e:
                                # Print error for debugging
                                print(f"DeepFace analysis error: {e}")
                                pass
                
                # Draw on full-size frame using cached results
                scale_factor = 1 / 0.4  # Inverse of resize factor
                
                # Draw face bounding boxes and names
                for (top, right, bottom, left), name in zip(face_locations_cache, face_names_cache):
                    # Scale back to full frame size
                    top = int(top * scale_factor)
                    right = int(right * scale_factor)
                    bottom = int(bottom * scale_factor)
                    left = int(left * scale_factor)
                    
                    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
                    
                    # Draw name label (simpler, analysis shown in overlay)
                    display_text = name
                    text_size = cv2.getTextSize(display_text, cv2.FONT_HERSHEY_DUPLEX, 0.7, 2)[0]
                    text_height = text_size[1] + 10
                    
                    # Draw background for name
                    cv2.rectangle(
                        frame, (left, bottom - text_height), (right, bottom), color, cv2.FILLED
                    )
                    
                    # Draw name
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(
                        frame, display_text, (left + 6, bottom - 10),
                        font, 0.7, (255, 255, 255), 2
                    )
                
                # Draw analysis overlay in top-left corner (if using DeepFace)
                # Show overlay even if analysis_cache is empty (will show "N/A" for missing data)
                if self.detection_model.get() == "deepface":
                    # If we have faces but no analysis yet, create placeholder entries
                    if not analysis_cache and face_names_cache:
                        for idx, name in enumerate(face_names_cache):
                            cache_key = name if name != "Unknown" else f"Face_{idx}"
                            analysis_cache[cache_key] = {
                                'emotion': 'Processing...',
                                'age': 0,
                                'gender': 'Processing...',
                                'race': 'Processing...'
                            }
                    
                    # Calculate overlay size based on number of people
                    num_people = len(analysis_cache) if analysis_cache else (len(face_names_cache) if face_names_cache else 1)
                    overlay_y = 10
                    overlay_x = 10
                    overlay_width = 320
                    overlay_height = min(300, 50 + num_people * 90)  # Dynamic height, increased for more info
                    
                    # Semi-transparent background
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (overlay_x, overlay_y), 
                                 (overlay_x + overlay_width, overlay_y + overlay_height), 
                                 (0, 0, 0), -1)
                    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
                    
                    # Draw title with border
                    title = "DeepFace Analysis"
                    cv2.putText(frame, title, (overlay_x + 10, overlay_y + 28),
                              cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 255), 2)
                    cv2.putText(frame, title, (overlay_x + 10, overlay_y + 28),
                              cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)
                    
                    # Draw analysis for each person (both recognized and unknown)
                    y_offset = overlay_y + 55
                    line_height = 22
                    for person_key, analysis_data in analysis_cache.items():
                        if y_offset + line_height * 5 > overlay_y + overlay_height - 10:
                            break  # Don't overflow overlay
                        
                        # Person name (highlighted)
                        display_name = person_key if person_key.startswith("Face_") else person_key
                        cv2.putText(frame, f"Person: {display_name}", 
                                  (overlay_x + 10, y_offset),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                        y_offset += line_height
                        
                        # Emotion
                        emotion = analysis_data.get('emotion', 'N/A')
                        cv2.putText(frame, f"  Emotion: {emotion}", 
                                  (overlay_x + 10, y_offset),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        y_offset += line_height
                        
                        # Age and Gender
                        age = analysis_data.get('age', 0)
                        gender = analysis_data.get('gender', 'N/A')
                        cv2.putText(frame, f"  Age: {age}y | Gender: {gender}", 
                                  (overlay_x + 10, y_offset),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        y_offset += line_height
                        
                        # Race (if available)
                        race = analysis_data.get('race', 'N/A')
                        if race != 'N/A':
                            cv2.putText(frame, f"  Race: {race}", 
                                      (overlay_x + 10, y_offset),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                            y_offset += line_height
                        
                        y_offset += 5  # Spacing between people
                        
                        # Race
                        race = analysis_data.get('race', 'N/A')
                        cv2.putText(frame, f"  Race: {race}", 
                                  (overlay_x + 10, y_offset),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        y_offset += line_height + 8  # Extra space between people
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img = img.resize((880, 660), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                
                video_label.imgtk = imgtk
                video_label.config(image=imgtk)
            
            if self.camera_running:
                camera_window.after(33, update_frame)  # ~30 FPS for better performance
        
        update_frame()
    
    def rotate_camera(self):
        """Rotate camera by 90 degrees (cycles: 0 -> 90 -> 180 -> 270 -> 0)."""
        current = self.camera_rotate.get()
        next_rotation = (current + 90) % 360
        self.camera_rotate.set(next_rotation)
        print(f"Camera rotated to {next_rotation} degrees")
    
    def stop_camera(self, window):
        """Stop the camera and close the window."""
        self.camera_running = False
        if self.video_capture:
            self.video_capture.release()
        
        # Disconnect Live API if active
        if self.live_api_enabled and self.gemini_live_api:
            self.gemini_live_api.disconnect()
            self.gemini_live_api = None
            self.live_api_enabled = False
        
        window.destroy()
    
    def start_smart_attendance(self):
        """Start smart attendance tracking with Google Sheets integration - uses YOLOv11 like Live Recognition."""
        # Re-check availability in case packages were installed after app startup
        try:
            from attendance_sheet import mark_present, get_present_students
            attendance_available = True
        except ImportError as e:
            attendance_available = False
            error_msg = (
                "Smart Attendance is not available.\n\n"
                f"Error: {str(e)}\n\n"
                "Please install required packages:\n\n"
                "pip install gspread oauth2client\n\n"
                "Note: You may see dependency warnings about google-auth versions,\n"
                "but the packages should still work. If issues persist, try:\n"
                "pip install --upgrade google-auth-oauthlib"
            )
            messagebox.showerror("Error", error_msg)
            return
        
        if not self.get_current_encodings():
            messagebox.showerror(
                "Error", "No trained model found! Please train the model first."
            )
            return
        
        # Check if it's a new day and reset if needed
        today = date.today()
        if self.attendance_date != today:
            self.seen_today = set()
            self.attendance_date = today
            print(f"New day detected - Attendance reset for {today}")
        
        # Archive students for today when Smart Attendance opens
        # Get trained person names from encodings (not from Column A)
        try:
            from attendance_sheet import archive_students_for_today
            current_encodings = self.get_current_encodings()
            if current_encodings:
                # Get unique trained person names
                trained_names = sorted(set(current_encodings.get("names", [])))
                print(f"Archiving {len(trained_names)} trained student names for today...")
                if archive_students_for_today(trained_names):
                    print(f"Successfully archived {len(trained_names)} student names with date")
                else:
                    print("Warning: Could not archive student names")
            else:
                print("Warning: No trained encodings found - cannot archive student names")
        except Exception as e:
            print(f"Error archiving students: {e}")
        
        camera_window = tk.Toplevel(self.root)
        camera_window.title("Smart Attendance - Face Recognition (YOLOv11)")
        camera_window.geometry("1200x800")
        camera_window.resizable(True, True)
        camera_window.configure(bg=COLORS["bg_primary"])
        camera_window.minsize(1000, 700)
        
        # Main container with horizontal split (like Live Recognition)
        main_container = tk.Frame(camera_window, bg=COLORS["bg_primary"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
        
        # Left side: Video frame
        left_panel = tk.Frame(main_container, bg=COLORS["bg_primary"])
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Video frame
        video_frame = tk.Frame(left_panel, bg=COLORS["bg_secondary"])
        video_frame.pack(fill=tk.BOTH, expand=True)
        
        # Video label
        video_label = tk.Label(video_frame, bg=COLORS["bg_secondary"])
        video_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right side: Attendance Status Panel
        right_panel = tk.Frame(main_container, bg=COLORS["bg_primary"], width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_panel.pack_propagate(False)
        
        # Attendance Status Section
        status_section = tk.Frame(right_panel, bg=COLORS["bg_secondary"], relief=tk.RAISED, bd=2)
        status_section.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        tk.Label(
            status_section,
            text="📋 Attendance Status",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Status info
        status_info = tk.Label(
            status_section,
            text="Students will be marked as 'Present'\nin Google Sheet when recognized.",
            font=("Segoe UI", 9),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_secondary"],
            justify=tk.LEFT,
            anchor=tk.W
        )
        status_info.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Attendance list frame with scrollbar
        list_frame = tk.Frame(status_section, bg=COLORS["bg_secondary"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        attendance_listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 10),
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
            selectbackground=COLORS["bg_hover"]
        )
        attendance_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=attendance_listbox.yview)
        
        # Control frame (bottom section - like Live Recognition)
        control_frame = tk.Frame(camera_window, bg=COLORS["bg_secondary"])
        control_frame.pack(fill=tk.X, padx=10, pady=(10, 10))
        
        # Top row of controls
        top_controls = tk.Frame(control_frame, bg=COLORS["bg_secondary"])
        top_controls.pack(fill=tk.X, padx=10, pady=10)
        
        # Status label (left side)
        status_label = tk.Label(
            top_controls,
            text=f"Smart Attendance Active (YOLOv11) - {len(self.seen_today)} student(s) marked",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        )
        status_label.pack(side=tk.LEFT, padx=10)
        
        # Camera controls (center) - like Live Recognition
        camera_controls_frame = tk.Frame(top_controls, bg=COLORS["bg_secondary"])
        camera_controls_frame.pack(side=tk.LEFT, padx=20, expand=True)
        
        # Flip Horizontal button
        flip_h_btn = tk.Button(
            camera_controls_frame,
            text="↔️ Flip H",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["bg_hover"],
            command=lambda: self.camera_flip_horizontal.set(not self.camera_flip_horizontal.get()),
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=6
        )
        flip_h_btn.pack(side=tk.LEFT, padx=5)
        
        # Flip Vertical button
        flip_v_btn = tk.Button(
            camera_controls_frame,
            text="↕️ Flip V",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["bg_hover"],
            command=lambda: self.camera_flip_vertical.set(not self.camera_flip_vertical.get()),
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=6
        )
        flip_v_btn.pack(side=tk.LEFT, padx=5)
        
        # Rotate button
        rotate_btn = tk.Button(
            camera_controls_frame,
            text="🔄 Rotate Camera",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["bg_hover"],
            command=self.rotate_camera,
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        )
        rotate_btn.pack(side=tk.LEFT, padx=5)
        
        # Right side buttons
        right_controls = tk.Frame(top_controls, bg=COLORS["bg_secondary"])
        right_controls.pack(side=tk.RIGHT, padx=10)
        
        # Check Spreadsheet button
        check_btn = tk.Button(
            right_controls,
            text="📋 Check Spreadsheet",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["bg_hover"],
            command=lambda: self._check_spreadsheet(attendance_listbox, status_label),
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        )
        check_btn.pack(side=tk.LEFT, padx=5)
        
        # Reset button
        reset_btn = tk.Button(
            right_controls,
            text="🔄 Reset Today",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["bg_hover"],
            command=lambda: self._reset_attendance(attendance_listbox, status_label),
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        )
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Stop button
        stop_btn = tk.Button(
            right_controls,
            text="⛔ Stop",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["bg_hover"],
            command=lambda: self.stop_camera(camera_window),
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        )
        stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.camera_running = True
        self.video_capture = cv2.VideoCapture(self.camera_index.get())
        
        if not self.video_capture.isOpened():
            messagebox.showerror("Error", f"Could not open camera {self.camera_index.get()}")
            camera_window.destroy()
            return
        
        # Performance optimization variables
        process_frame_count = 0
        face_locations_cache = []
        face_names_cache = []
        
        # Detection history for accuracy - require multiple consistent detections
        # Format: {(face_location_tuple): {"name": "Name", "count": 5, "display_name": "Name", "display_count": 3, "last_seen": frame_count}}
        detection_history = {}  # Track detections per face location
        REQUIRED_CONSISTENT_DETECTIONS = 8  # Require 8 consistent detections before marking (balanced for accuracy)
        REQUIRED_DISPLAY_DETECTIONS = 3  # Require 3 consistent detections before showing name on screen (prevents flickering)
        DETECTION_TIMEOUT = 15  # Reset detection if face not seen for 15 frames
        
        # Check date periodically and reset if new day
        def check_date_reset():
            """Check if it's a new day and reset attendance if needed."""
            today = date.today()
            if self.attendance_date != today:
                self.seen_today = set()
                self.attendance_date = today
                attendance_listbox.delete(0, tk.END)
                status_label.config(text=f"Smart Attendance Active (YOLOv11) - 0 student(s) marked (New Day)")
                print(f"New day detected - Attendance automatically reset for {today}")
            if self.camera_running:
                camera_window.after(60000, check_date_reset)  # Check every minute
        
        # Start date checking
        check_date_reset()
        
        def update_frame():
            nonlocal process_frame_count, face_locations_cache, face_names_cache, detection_history
            
            if not self.camera_running:
                return
            
            ret, frame = self.video_capture.read()
            if not ret:
                if self.camera_running:
                    camera_window.after(33, update_frame)
                return
            
            # Apply camera transformations
            if self.camera_flip_horizontal.get():
                frame = cv2.flip(frame, 1)
            if self.camera_flip_vertical.get():
                frame = cv2.flip(frame, 0)
            rotation = self.camera_rotate.get()
            if rotation == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif rotation == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif rotation == 270:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
            # Process frames (same logic as Live Recognition)
            process_frame_count += 1
            should_process = (process_frame_count % 3 == 0)  # Process every 3rd frame
                
            if should_process:
                # Resize frame for faster processing
                small_frame = cv2.resize(frame, (0, 0), fx=0.4, fy=0.4)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                
                # Get YOLOv11 detector (already set at start of function)
                detector = self.get_detector()
                
                face_locations_cache = []
                face_names_cache = []
                
                if detector:
                    try:
                        # Detect faces using YOLOv11 detector (returns face locations directly)
                        face_locations_cache = detector.detect_faces(rgb_small_frame)
                    except Exception as e:
                        print(f"Face detection error: {e}")
                        face_locations_cache = []
                
                # Recognize faces with improved accuracy using detection history
                current_encodings = self.get_current_encodings()
                if current_encodings and face_locations_cache:
                    # Get face encodings
                    face_encodings = face_recognition.face_encodings(
                        rgb_small_frame, face_locations_cache
                    )
                    
                    # Clean up old detection history (faces not seen recently)
                    current_frame = process_frame_count
                    keys_to_remove = []
                    for face_key, history in detection_history.items():
                        if current_frame - history["last_seen"] > DETECTION_TIMEOUT:
                            keys_to_remove.append(face_key)
                    for key in keys_to_remove:
                        del detection_history[key]
                    
                    # Process each detected face
                    for idx, (face_location, face_encoding) in enumerate(zip(face_locations_cache, face_encodings)):
                        # Use face location as key (rounded to handle small movements)
                        face_key = tuple(int(coord / 10) * 10 for coord in face_location)
                        
                        # Recognize the face with stricter threshold
                        name = self.recognize_face_in_frame(face_encoding)
                        name = name if name else "Unknown"
                        
                        # Update detection history
                        if name != "Unknown":
                            if face_key in detection_history:
                                # Check if same person
                                if detection_history[face_key]["name"] == name:
                                    # Increment count
                                    detection_history[face_key]["count"] += 1
                                    detection_history[face_key]["last_seen"] = current_frame
                                    
                                    # Update display name only after consistent detections (prevents flickering)
                                    if detection_history[face_key]["count"] >= REQUIRED_DISPLAY_DETECTIONS:
                                        # Stable detection - update display name
                                        if detection_history[face_key].get("display_name") != name:
                                            detection_history[face_key]["display_name"] = name
                                            detection_history[face_key]["display_count"] = 1
                                        else:
                                            detection_history[face_key]["display_count"] += 1
                                else:
                                    # Different person detected at same location - reset completely
                                    detection_history[face_key] = {
                                        "name": name,
                                        "count": 1,
                                        "display_name": "Unknown",  # Don't show name until stable
                                        "display_count": 0,
                                        "last_seen": current_frame
                                    }
                            else:
                                # New face detected - start with "Unknown" display
                                detection_history[face_key] = {
                                    "name": name,
                                    "count": 1,
                                    "display_name": "Unknown",  # Don't show name until stable
                                    "display_count": 0,
                                    "last_seen": current_frame
                                }
                            
                            # Get the display name (stabilized)
                            display_name = detection_history[face_key].get("display_name", "Unknown")
                            face_names_cache.append(display_name)
                            
                            # Only mark attendance after many consistent detections (high accuracy requirement)
                            if (detection_history[face_key]["count"] >= REQUIRED_CONSISTENT_DETECTIONS and 
                                name not in self.seen_today):
                                self.seen_today.add(name)
                                # Update UI
                                attendance_listbox.insert(tk.END, f"✓ {name}")
                                attendance_listbox.see(tk.END)
                                status_label.config(
                                    text=f"Smart Attendance Active (YOLOv11) - {len(self.seen_today)} student(s) marked"
                                )
                                
                                # Save the frame when marking attendance (with face recognition box and date)
                                try:
                                    # Use relative path - users can change this to their preferred location
                                    attendance_photos_base_dir = Path("attendance_photos")
                                    
                                    # Create a folder for today's date (YYYY-MM-DD format)
                                    today_date = date.today().strftime("%Y-%m-%d")
                                    attendance_photos_dir = attendance_photos_base_dir / today_date
                                    attendance_photos_dir.mkdir(parents=True, exist_ok=True)
                                    
                                    # Create a copy of the frame to draw on
                                    frame_to_save = frame.copy()
                                    
                                    # Scale face location back to full frame size (detection was done on small_frame)
                                    scale_factor = 1 / 0.4
                                    top = int(face_location[0] * scale_factor)
                                    right = int(face_location[1] * scale_factor)
                                    bottom = int(face_location[2] * scale_factor)
                                    left = int(face_location[3] * scale_factor)
                                    
                                    # Draw bounding box (green for recognized person)
                                    color = (0, 255, 0)  # Green
                                    cv2.rectangle(frame_to_save, (left, top), (right, bottom), color, 3)
                                    
                                    # Draw name label with background
                                    display_text = f"{name} ✓"
                                    font = cv2.FONT_HERSHEY_DUPLEX
                                    text_size = cv2.getTextSize(display_text, font, 0.7, 2)[0]
                                    text_height = text_size[1] + 10
                                    
                                    # Draw background rectangle for name
                                    cv2.rectangle(
                                        frame_to_save, (left, bottom - text_height), (right, bottom), color, cv2.FILLED
                                    )
                                    
                                    # Draw name text
                                    cv2.putText(
                                        frame_to_save, display_text, (left + 6, bottom - 10),
                                        font, 0.7, (255, 255, 255), 2
                                    )
                                    
                                    # Draw date in top-right corner
                                    date_text = today_date
                                    date_font = cv2.FONT_HERSHEY_SIMPLEX
                                    date_text_size = cv2.getTextSize(date_text, date_font, 0.8, 2)[0]
                                    
                                    # Get frame dimensions
                                    frame_height, frame_width = frame_to_save.shape[:2]
                                    
                                    # Position date in top-right corner with padding
                                    date_x = frame_width - date_text_size[0] - 20
                                    date_y = 35
                                    
                                    # Draw background rectangle for date
                                    date_bg_padding = 10
                                    cv2.rectangle(
                                        frame_to_save,
                                        (date_x - date_bg_padding, date_y - date_text_size[1] - date_bg_padding),
                                        (date_x + date_text_size[0] + date_bg_padding, date_y + date_bg_padding),
                                        (0, 0, 0),
                                        cv2.FILLED
                                    )
                                    
                                    # Draw date text
                                    cv2.putText(
                                        frame_to_save, date_text, (date_x, date_y),
                                        date_font, 0.8, (255, 255, 255), 2
                                    )
                                    
                                    # Create filename from person's name (sanitize for filesystem)
                                    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
                                    safe_name = safe_name.replace(' ', '_')
                                    
                                    # Use person's name as filename, add number if file exists
                                    base_filename = f"{safe_name}.jpg"
                                    filepath = attendance_photos_dir / base_filename
                                    
                                    # If file exists, add a number suffix
                                    counter = 1
                                    while filepath.exists():
                                        filename_with_counter = f"{safe_name}_{counter}.jpg"
                                        filepath = attendance_photos_dir / filename_with_counter
                                        counter += 1
                                    
                                    # Save the annotated frame
                                    cv2.imwrite(str(filepath), frame_to_save)
                                    print(f"Saved attendance photo: {filepath}")
                                except Exception as e:
                                    print(f"Warning: Could not save attendance photo for {name}: {e}")
                                    import traceback
                                    print(traceback.format_exc())
                                
                                # Mark in Google Sheet (non-blocking)
                                try:
                                    from attendance_sheet import mark_present
                                    print(f"Marking '{name}' as present (confirmed after {detection_history[face_key]['count']} detections)")
                                    mark_present(name)
                                except Exception as e:
                                    import traceback
                                    error_msg = f"Error marking attendance for {name}:\n{str(e)}\n\n{traceback.format_exc()}"
                                    print(error_msg)
                                    messagebox.showerror("Attendance Error", f"Failed to update Google Sheet for {name}:\n{str(e)}")
                        else:
                            # Unknown face - reset display but keep history for a bit (in case it's temporary)
                            if face_key in detection_history:
                                # If we had a name before, reset display but keep counting
                                if detection_history[face_key].get("display_name") != "Unknown":
                                    detection_history[face_key]["display_name"] = "Unknown"
                                    detection_history[face_key]["display_count"] = 0
                                # Reset the name count if too many unknowns
                                if detection_history[face_key]["count"] > 0:
                                    detection_history[face_key]["count"] = max(0, detection_history[face_key]["count"] - 2)  # Decay faster
                            face_names_cache.append("Unknown")
            
            # Always draw on full-size frame (even if not processing this frame)
            scale_factor = 1 / 0.4
            
            for (top, right, bottom, left), name in zip(face_locations_cache, face_names_cache):
                top = int(top * scale_factor)
                right = int(right * scale_factor)
                bottom = int(bottom * scale_factor)
                left = int(left * scale_factor)
                
                # Green for recognized, red for unknown
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
                
                # Draw name label
                display_text = name
                if name != "Unknown" and name in self.seen_today:
                    display_text = f"{name} ✓"
                
                text_size = cv2.getTextSize(display_text, cv2.FONT_HERSHEY_DUPLEX, 0.7, 2)[0]
                text_height = text_size[1] + 10
                
                cv2.rectangle(
                    frame, (left, bottom - text_height), (right, bottom), color, cv2.FILLED
                )
                
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(
                    frame, display_text, (left + 6, bottom - 10),
                    font, 0.7, (255, 255, 255), 2
                )
            
            # Always display frame (even if not processing faces this frame)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((880, 660), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            
            video_label.imgtk = imgtk
            video_label.config(image=imgtk)
            
            if self.camera_running:
                camera_window.after(33, update_frame)
        
        update_frame()
    
    def _check_spreadsheet(self, listbox, status_label):
        """Check spreadsheet for present students and update UI."""
        try:
            from attendance_sheet import get_present_students
        except ImportError as e:
            messagebox.showerror("Error", f"Attendance module not available:\n{e}")
            return
        
        try:
            # Get all present students from spreadsheet
            present_students = get_present_students()
            
            # Update seen_today with students found in spreadsheet
            new_students = present_students - self.seen_today
            self.seen_today.update(present_students)
            
            # Update listbox
            listbox.delete(0, tk.END)
            for student in sorted(self.seen_today):
                listbox.insert(tk.END, f"✓ {student}")
            
            # Update status label
            status_label.config(
                text=f"Smart Attendance Active (YOLOv11) - {len(self.seen_today)} student(s) marked"
            )
            
            # Show message if new students were found
            if new_students:
                messagebox.showinfo(
                    "Spreadsheet Updated",
                    f"Found {len(new_students)} new student(s) marked present:\n" +
                    "\n".join(sorted(new_students))
                )
            else:
                messagebox.showinfo(
                    "Spreadsheet Check",
                    f"Spreadsheet checked. {len(self.seen_today)} student(s) marked present."
                )
            
            print(f"Spreadsheet checked - {len(self.seen_today)} students marked present")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check spreadsheet:\n{e}")
            print(f"Error checking spreadsheet: {e}")
    
    def _reset_attendance(self, listbox, status_label):
        """Reset today's attendance tracking."""
        self.seen_today = set()
        listbox.delete(0, tk.END)
        status_label.config(text="Smart Attendance Active (YOLOv11) - 0 student(s) marked")
        print("Attendance reset - students can be marked again")
    
    def toggle_live_api(self):
        """Toggle Gemini Live API on/off."""
        # Reload API key from settings to ensure we have the latest value
        self.load_gemini_api_key()
        
        api_key = self.gemini_api_key.get().strip()
        if not api_key:
            messagebox.showerror(
                "API Key Required",
                "Please set your Gemini API key in Settings first.\n\n"
                "Get your free API key from:\n"
                "https://makersuite.google.com/app/apikey"
            )
            return
        
        if not self.live_api_enabled:
            # Enable Live API
            try:
                # Use the current API key value
                api_key = self.gemini_api_key.get().strip()
                if not api_key:
                    messagebox.showerror("Error", "API key is empty. Please set it in Settings.")
                    return
                
                print(f"Connecting to Gemini Live API with key (length: {len(api_key)} characters)...")
                self.gemini_live_api = GeminiLiveAPI(api_key)
                
                # Set callbacks
                self.gemini_live_api.set_callbacks(
                    on_connect=lambda: self.root.after(0, lambda: self._on_live_api_connect()),
                    on_disconnect=lambda: self.root.after(0, lambda: self._on_live_api_disconnect()),
                    on_error=lambda e: self.root.after(0, lambda err=e: self._on_live_api_error(err)),
                    on_message=lambda msg: self.root.after(0, lambda m=msg: self._on_live_api_message(m))
                )
                
                # Connect
                self.gemini_live_api.connect()
                
                # Wait a moment for connection
                self.root.after(1000, lambda: self._start_live_api_streaming())
                
            except Exception as e:
                messagebox.showerror(
                    "Live API Error",
                    f"Failed to connect to Gemini Live API:\n{str(e)}\n\n"
                    "Make sure:\n"
                    "1. Your API key is valid\n"
                    "2. PyAudio is installed: pip install pyaudio\n"
                    "3. websockets is installed: pip install websockets"
                )
                if self.gemini_live_api:
                    self.gemini_live_api.disconnect()
                    self.gemini_live_api = None
        else:
            # Disable Live API
            if self.gemini_live_api:
                self.gemini_live_api.disconnect()
                self.gemini_live_api = None
            self.live_api_enabled = False
            if hasattr(self, 'live_api_toggle_btn'):
                self.live_api_toggle_btn.config(
                    text="🎙️ Live Call: OFF",
                    bg=COLORS["bg_tertiary"]
                )
    
    def _start_live_api_streaming(self):
        """Start audio streaming for Live API."""
        # Check if widgets still exist (window might be closed)
        try:
            if not hasattr(self, 'live_api_status_label') or not self.live_api_status_label.winfo_exists():
                print("⚠️ Live API window closed, aborting streaming start")
                return
        except:
            print("⚠️ Live API window closed, aborting streaming start")
            return
        
        if self.gemini_live_api and self.gemini_live_api.is_connected:
            try:
                print("🎤 Starting audio streaming...")
                self.gemini_live_api.start_streaming()
                self.live_api_enabled = True
                try:
                    if hasattr(self, 'live_api_status_label') and self.live_api_status_label.winfo_exists():
                        self.live_api_status_label.config(
                            text="🟢 Connected - Streaming Audio...",
                            fg=COLORS["success"]
                        )
                    if hasattr(self, 'live_api_toggle_btn') and self.live_api_toggle_btn.winfo_exists():
                        self.live_api_toggle_btn.config(
                            text="🎙️ Live Call: ON",
                            bg=COLORS["bg_tertiary"]
                        )
                    # Update transcript
                    self._update_live_api_transcript("🎤 Audio streaming started. You can now speak!", is_response=False)
                except Exception as widget_error:
                    print(f"⚠️ Widget update error (window may be closed): {widget_error}")
                print("✓ Audio streaming started successfully")
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Failed to start streaming: {error_msg}")
                try:
                    if hasattr(self, 'live_api_status_label') and self.live_api_status_label.winfo_exists():
                        self.live_api_status_label.config(
                            text=f"❌ Streaming Error: {error_msg[:40]}...",
                            fg=COLORS["error"]
                        )
                    messagebox.showerror("Live API Error", f"Failed to start streaming:\n{error_msg}")
                except:
                    pass
                if self.gemini_live_api:
                    self.gemini_live_api.disconnect()
                    self.gemini_live_api = None
        else:
            print("⚠️ Cannot start streaming: Not connected to Live API")
            try:
                # Check if window still exists by trying to access a widget
                if hasattr(self, 'live_api_status_label'):
                    try:
                        _ = self.live_api_status_label.winfo_exists()
                        self.live_api_status_label.config(
                            text="⚠️ Not Connected - Retrying...",
                            fg=COLORS["warning"]
                        )
                        # Retry connection after a delay (only if window still exists)
                        self.root.after(2000, lambda: self._start_live_api_streaming())
                    except tk.TclError:
                        print("⚠️ Window closed, stopping retry attempts")
                        return
            except Exception as e:
                print(f"⚠️ Error checking window status: {e}")
                return
    
    def _on_live_api_connect(self):
        """Callback when Live API connects."""
        print("✓ Connected to Gemini Live API")
        try:
            if hasattr(self, 'live_api_status_label') and self.live_api_status_label.winfo_exists():
                self.live_api_status_label.config(
                    text="🟢 Connected - Listening...",
                    fg=COLORS["success"]
                )
            if hasattr(self, 'live_api_toggle_btn') and self.live_api_toggle_btn.winfo_exists():
                self.live_api_toggle_btn.config(
                    text="🎙️ Live Call: ON",
                    bg=COLORS["bg_tertiary"]
                )
        except Exception as e:
            print(f"⚠️ Error updating UI on connect: {e}")
    
    def _on_live_api_disconnect(self):
        """Callback when Live API disconnects."""
        print("✗ Disconnected from Gemini Live API")
        self.live_api_enabled = False
        try:
            if hasattr(self, 'live_api_status_label') and self.live_api_status_label.winfo_exists():
                self.live_api_status_label.config(
                    text="🔴 Disconnected",
                    fg=COLORS["error"]
                )
            if hasattr(self, 'live_api_toggle_btn') and self.live_api_toggle_btn.winfo_exists():
                self.live_api_toggle_btn.config(
                    text="🎙️ Live Call: OFF",
                    bg=COLORS["bg_tertiary"]
                )
        except Exception as e:
            print(f"⚠️ Error updating UI on disconnect: {e}")
    
    def _on_live_api_error(self, error):
        """Callback when Live API error occurs."""
        error_msg = str(error)
        print(f"❌ Live API Error: {error_msg}")
        try:
            if hasattr(self, 'live_api_status_label') and self.live_api_status_label.winfo_exists():
                self.live_api_status_label.config(
                    text=f"❌ Error: {error_msg[:50]}...",
                    fg=COLORS["error"]
                )
            messagebox.showerror("Live API Error", f"An error occurred:\n{error_msg}")
        except Exception as e:
            print(f"⚠️ Error showing error message: {e}")
    
    def _on_live_api_message(self, message):
        """Callback when Live API message is received."""
        try:
            # Handle different message types
            if isinstance(message, dict):
                # Handle text responses
                if "text" in message:
                    text = message["text"]
                    print(f"💬 Gemini Response: {text}")
                    self._update_live_api_transcript(f"Gemini: {text}", is_response=True)
                
                # Handle standard API response format
                if "candidates" in message:
                    candidates = message.get("candidates", [])
                    for candidate in candidates:
                        if "content" in candidate:
                            content = candidate["content"]
                            if "parts" in content:
                                for part in content["parts"]:
                                    if "text" in part:
                                        text = part["text"]
                                        print(f"💬 Gemini Response: {text}")
                                        self._update_live_api_transcript(f"Gemini: {text}", is_response=True)
                
                # Check for server content with transcriptions or responses
                if "serverContent" in message:
                    server_content = message["serverContent"]
                    
                    # Handle transcriptions (what user said)
                    if "modelTurn" in server_content:
                        model_turn = server_content["modelTurn"]
                        if "parts" in model_turn:
                            for part in model_turn["parts"]:
                                if "text" in part:
                                    text = part["text"]
                                    print(f"📝 Gemini Response: {text}")
                                    self._update_live_api_transcript(f"Gemini: {text}", is_response=True)
                    
                    # Handle user transcriptions
                    if "clientContent" in server_content:
                        client_content = server_content["clientContent"]
                        if "turns" in client_content:
                            for turn in client_content["turns"]:
                                if "parts" in turn:
                                    for part in turn["parts"]:
                                        if "text" in part:
                                            text = part["text"]
                                            print(f"🎤 You said: {text}")
                                            self._update_live_api_transcript(f"You: {text}", is_response=False)
                
                # Update status to show activity
                if hasattr(self, 'live_api_status_label'):
                    current_text = self.live_api_status_label.cget("text")
                    if "🟢" in current_text:
                        self.live_api_status_label.config(
                            text="🟢 Connected - Active ✨",
                            fg=COLORS["success"]
                        )
        except Exception as e:
            print(f"Error processing Live API message: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_live_api_transcript(self, text, is_response=False):
        """Update the transcript display in the live camera window."""
        if hasattr(self, 'live_api_transcript_text'):
            try:
                # Enable editing
                self.live_api_transcript_text.config(state=tk.NORMAL)
                
                # Configure tags if not already done
                if not hasattr(self, '_transcript_tags_configured'):
                    self.live_api_transcript_text.tag_config("user", foreground=COLORS["accent_purple"], font=("Segoe UI", 9, "bold"))
                    self.live_api_transcript_text.tag_config("response", foreground=COLORS["accent_blue"], font=("Segoe UI", 9, "bold"))
                    self._transcript_tags_configured = True
                
                # Get current content
                current = self.live_api_transcript_text.get("1.0", tk.END).strip()
                
                # Remove initial message if present
                if "💡 Start a Live Call" in current:
                    self.live_api_transcript_text.delete("1.0", tk.END)
                    current = ""
                
                # Add new message
                tag = "response" if is_response else "user"
                
                # Insert new text
                if current:
                    self.live_api_transcript_text.insert(tk.END, "\n")
                self.live_api_transcript_text.insert(tk.END, text + "\n", tag)
                
                # Auto-scroll to bottom
                self.live_api_transcript_text.see(tk.END)
                
                # Limit transcript length (keep last 50 lines)
                lines = self.live_api_transcript_text.get("1.0", tk.END).split("\n")
                if len(lines) > 50:
                    self.live_api_transcript_text.delete("1.0", f"{len(lines) - 50}.0")
                
                # Disable editing to prevent user modification
                self.live_api_transcript_text.config(state=tk.DISABLED)
            except Exception as e:
                print(f"Error updating transcript: {e}")
                import traceback
                traceback.print_exc()
    
    def load_gemini_api_key(self):
        """Load Gemini API key from file if exists."""
        try:
            key_file = Path("output/gemini_api_key.txt")
            if key_file.exists():
                with key_file.open("r", encoding="utf-8") as f:
                    api_key = f.read().strip()
                    if api_key:
                        self.gemini_api_key.set(api_key)
                        print(f"✓ Gemini API key loaded successfully (length: {len(api_key)} characters)")
                        print(f"   File location: {key_file.absolute()}")
                        return True
                    else:
                        print("⚠️ API key file exists but is empty")
                        self.gemini_api_key.set("")  # Set to empty
                        return False
            else:
                print(f"ℹ️ No saved API key found at: {key_file.absolute()}")
                print("   Please set it in Settings.")
                return False
        except Exception as e:
            print(f"❌ Error loading Gemini API key: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_gemini_api_key(self):
        """Save Gemini API key to file."""
        try:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            key_file = output_dir / "gemini_api_key.txt"
            api_key = self.gemini_api_key.get().strip()
            
            # Write the API key to file
            with key_file.open("w", encoding="utf-8") as f:
                f.write(api_key)
            
            # Verify it was written correctly
            if key_file.exists():
                with key_file.open("r", encoding="utf-8") as f:
                    saved_key = f.read().strip()
                if saved_key == api_key:
                    if api_key:
                        print(f"✓ Gemini API key saved and verified successfully (length: {len(api_key)} characters)")
                        print(f"   File location: {key_file.absolute()}")
                    else:
                        print(f"✓ API key cleared (file updated)")
                    return True
                else:
                    print(f"⚠️ Warning: API key verification failed - saved: '{saved_key[:10]}...', expected: '{api_key[:10] if api_key else '(empty)'}...'")
                    return False
            else:
                print(f"⚠️ Warning: API key file was not created at {key_file.absolute()}")
                return False
        except Exception as e:
            print(f"❌ Error saving Gemini API key: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_image(self):
        """Test recognition on a single image or video."""
        if not self.get_current_encodings():
            messagebox.showerror(
                "Error", "No trained model found! Please train the model first."
            )
            return
        
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
            ("Video files", "*.mp4 *.avi *.mov *.mkv"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select Image or Video to Test",
            filetypes=filetypes
        )
        
        if file_path:
            file_ext = Path(file_path).suffix.lower()
            video_extensions = {'.mp4', '.avi', '.mov', '.mkv'}
            
            if file_ext in video_extensions:
                # Process video
                self.test_video(file_path)
            else:
                # Process image
                try:
                    image = self.convert_image_to_rgb(file_path)
                    
                    detector = self.get_detector()
                    face_locations = detector.detect_faces(image)
                    
                    # Get encoding model type (HOG -> small, CNN -> large)
                    encoding_model = "small" if self.model_type.get() == "hog" else "large"
                    face_encodings = face_recognition.face_encodings(
                        image, face_locations, model=encoding_model
                    )
                    
                    from PIL import ImageDraw, ImageFont
                    pillow_image = Image.fromarray(image)
                    draw = ImageDraw.Draw(pillow_image)
                    
                    try:
                        font_size = max(20, int(image.shape[0] / 30))
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except:
                        try:
                            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
                        except:
                            font = ImageFont.load_default()
                    
                    # Get DeepFace analyzer if using DeepFace model
                    deepface_analyzer = None
                    if self.detection_model.get() == "deepface":
                        try:
                            deepface_analyzer = self.get_detector()
                        except:
                            pass
                    
                    for bounding_box, unknown_encoding in zip(face_locations, face_encodings):
                        name = self.recognize_face_in_frame(unknown_encoding)
                        if not name:
                            name = "Unknown"
                        
                        top, right, bottom, left = bounding_box
                        color = "blue" if name != "Unknown" else "red"
                        
                        draw.rectangle(((left, top), (right, bottom)), outline=color, width=4)
                        
                        # Prepare display text
                        display_text = name
                        
                        # Add DeepFace analysis if available
                        if deepface_analyzer and name != "Unknown":
                            try:
                                # Extract face region
                                face_roi = image[top:bottom, left:right]
                                if face_roi.size > 0:
                                    import tempfile
                                    import os
                                    temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg')
                                    os.close(temp_fd)
                                    Image.fromarray(face_roi).save(temp_path, 'JPEG')
                                    
                                    analysis = deepface_analyzer.analyze_face(
                                        temp_path,
                                        actions=['emotion', 'age', 'gender', 'race']
                                    )
                                    
                                    if analysis:
                                        # Apply calibration if available
                                        if self.deepface_calibrator and name != "Unknown":
                                            try:
                                                analysis = self.deepface_calibrator.calibrate_result(name, analysis)
                                            except Exception as e:
                                                print(f"Calibration error: {e}")
                                        
                                        emotion = analysis.get('dominant_emotion', 'N/A')
                                        age = int(analysis.get('age', 0))
                                        gender = analysis.get('dominant_gender', 'N/A')
                                        race = analysis.get('dominant_race', 'N/A')
                                        
                                        display_text = f"{name}\n{emotion} | {age}y | {gender} | {race}"
                                    
                                    os.remove(temp_path)
                            except:
                                pass
                        
                        text_y = max(0, top - 30)
                        
                        try:
                            bbox = draw.textbbox((left, text_y), display_text.split('\n')[0], font=font)
                            text_left, text_top, text_right, text_bottom = bbox
                        except:
                            text_left, text_top, text_right, text_bottom = draw.textbbox(
                                (left, text_y), display_text.split('\n')[0]
                            )
                        
                        # Calculate height for multi-line text
                        lines = display_text.split('\n')
                        line_height = 25
                        text_height = len(lines) * line_height
                        
                        padding = 5
                        draw.rectangle(
                            ((text_left - padding, text_top - padding), 
                             (text_right + padding, text_top + text_height + padding)),
                            fill=color,
                            outline=color,
                        )
                        
                        # Draw text (handle multi-line)
                        current_y = text_top
                        for line in display_text.split('\n'):
                            draw.text(
                                (text_left, current_y),
                                line,
                                fill="white",
                                font=font,
                            )
                            current_y += line_height
                    
                    self.show_result_image(pillow_image, file_path)
                
                except Exception as e:
                    import traceback
                    error_msg = f"Failed to process image: {str(e)}\n\n"
                    error_msg += "Make sure:\n"
                    error_msg += "1. The image contains clear faces\n"
                    error_msg += "2. You have trained the model first\n"
                    error_msg += "3. The image format is supported (JPG, PNG, etc.)"
                    messagebox.showerror("Error", error_msg)
                    print(f"Full error: {traceback.format_exc()}")
    
    def test_video(self, video_path):
        """Test recognition on a video file."""
        # Create video processing window
        video_window = tk.Toplevel(self.root)
        video_window.title("Video Recognition")
        video_window.geometry("1000x700")
        video_window.configure(bg=COLORS["bg_primary"])
        
        # Video display
        video_label = tk.Label(video_window, bg=COLORS["bg_secondary"])
        video_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control frame
        control_frame = tk.Frame(video_window, bg=COLORS["bg_secondary"], height=60)
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        control_frame.pack_propagate(False)
        
        status_label = tk.Label(
            control_frame,
            text="🎬 Processing Video...",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        )
        status_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        stop_btn = tk.Button(
            control_frame,
            text="Stop",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            command=lambda: self.stop_video_processing(video_window),
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8
        )
        stop_btn.pack(side=tk.RIGHT, padx=20, pady=15)
        
        self.video_processing = True
        
        def process_video_frames():
            try:
                cap = cv2.VideoCapture(str(video_path))
                if not cap.isOpened():
                    messagebox.showerror("Error", f"Could not open video: {video_path}")
                    video_window.destroy()
                    return
                
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_delay = int(1000 / fps) if fps > 0 else 33
                
                detector = self.get_detector()
                
                def process_next_frame():
                    if not self.video_processing:
                        cap.release()
                        video_window.destroy()
                        return
                    
                    ret, frame = cap.read()
                    if not ret:
                        cap.release()
                        status_label.config(text="✓ Video processing complete")
                        return
                    
                    # Resize for faster processing
                    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                    
                    # Detect and recognize faces
                    face_locations = detector.detect_faces(rgb_small_frame)
                    # Get encoding model type (HOG -> small, CNN -> large)
                    encoding_model = "small" if self.model_type.get() == "hog" else "large"
                    face_encodings = face_recognition.face_encodings(
                        rgb_small_frame, face_locations, model=encoding_model
                    )
                    
                    face_names = []
                    for face_encoding in face_encodings:
                        name = self.recognize_face_in_frame(face_encoding)
                        face_names.append(name if name else "Unknown")
                    
                    # Draw on full frame
                    scale_factor = 2
                    for (top, right, bottom, left), name in zip(face_locations, face_names):
                        top = int(top * scale_factor)
                        right = int(right * scale_factor)
                        bottom = int(bottom * scale_factor)
                        left = int(left * scale_factor)
                        
                        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                        cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
                        
                        cv2.rectangle(
                            frame, (left, bottom - 40), (right, bottom), color, cv2.FILLED
                        )
                        font = cv2.FONT_HERSHEY_DUPLEX
                        cv2.putText(
                            frame, name, (left + 6, bottom - 10),
                            font, 0.7, (255, 255, 255), 2
                        )
                    
                    # Display frame
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    img = img.resize((980, 600), Image.Resampling.LANCZOS)
                    imgtk = ImageTk.PhotoImage(image=img)
                    
                    video_label.imgtk = imgtk
                    video_label.config(image=imgtk)
                    
                    # Schedule next frame
                    video_window.after(frame_delay, process_next_frame)
                
                process_next_frame()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process video: {str(e)}")
                video_window.destroy()
        
        threading.Thread(target=process_video_frames, daemon=True).start()
    
    def stop_video_processing(self, window):
        """Stop video processing."""
        self.video_processing = False
        window.destroy()
    
    def show_result_image(self, image, original_path):
        """Display result image in a modern Tkinter window."""
        result_window = tk.Toplevel(self.root)
        result_window.title("Face Recognition Result")
        result_window.configure(bg=COLORS["bg_primary"])
        
        img_width, img_height = image.size
        max_width = self.root.winfo_screenwidth() - 100
        max_height = self.root.winfo_screenheight() - 150
        
        scale = min(max_width / img_width, max_height / img_height, 1.0)
        if scale < 1.0:
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(image)
        
        img_label = tk.Label(result_window, image=photo, bg=COLORS["bg_primary"])
        img_label.image = photo
        img_label.pack(padx=10, pady=10)
        
        info_frame = tk.Frame(result_window, bg=COLORS["bg_secondary"])
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        file_name = os.path.basename(original_path)
        info_label = tk.Label(
            info_frame,
            text=f"📄 {file_name}",
            font=("Segoe UI", 10),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_secondary"]
        )
        info_label.pack(pady=10)
        
        button_frame = tk.Frame(result_window, bg=COLORS["bg_primary"])
        button_frame.pack(pady=10)
        
        save_btn = tk.Button(
            button_frame,
            text="💾 Save Result",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            command=lambda: self.save_result_image(image, original_path),
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Button(
            button_frame,
            text="Close",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            command=result_window.destroy,
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        )
        close_btn.pack(side=tk.LEFT, padx=5)
    
    def save_result_image(self, image, original_path):
        """Save the result image with face recognition labels."""
        filetypes = [
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg"),
            ("All files", "*.*")
        ]
        
        default_name = os.path.splitext(os.path.basename(original_path))[0] + "_recognized"
        save_path = filedialog.asksaveasfilename(
            title="Save Result Image",
            defaultextension=".png",
            initialfile=default_name,
            filetypes=filetypes
        )
        
        if save_path:
            try:
                image.save(save_path)
                messagebox.showinfo("Success", f"Result saved to:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {str(e)}")
    
    def view_registered_people(self):
        """Show a window with list of registered people."""
        window = tk.Toplevel(self.root)
        window.title("Registered People")
        window.geometry("500x600")
        window.configure(bg=COLORS["bg_primary"])
        
        header = tk.Frame(window, bg=COLORS["bg_secondary"], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="Registered People",
            font=("Segoe UI", 24, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"],
            pady=28
        ).pack()
        
        content = tk.Frame(window, bg=COLORS["bg_primary"])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        scrollbar = tk.Scrollbar(content)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(
            content,
            yscrollcommand=scrollbar.set,
            font=("Segoe UI", 12),
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            selectbackground=COLORS["accent_blue"],
            selectforeground=COLORS["text_primary"],
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            activestyle='none'
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        current_encodings = self.get_current_encodings()
        if current_encodings:
            people = sorted(set(current_encodings["names"]))
            for person in people:
                count = current_encodings["names"].count(person)
                listbox.insert(tk.END, f"👤 {person} ({count} encoding(s))")
        else:
            listbox.insert(tk.END, "No registered people")
        
        close_btn = tk.Button(
            window,
            text="Close",
            command=window.destroy,
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8
        )
        close_btn.pack(pady=15)
    
    def show_settings(self):
        """Show settings window with modern dark theme."""
        window = tk.Toplevel(self.root)
        window.title("Settings")
        window.geometry("550x600")
        window.configure(bg=COLORS["bg_primary"])
        window.transient(self.root)  # Make it modal
        window.grab_set()  # Focus on this window
        
        header = tk.Frame(window, bg=COLORS["bg_secondary"], height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="⚙️ Settings",
            font=("Segoe UI", 20, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"],
            pady=20
        ).pack()
        
        content = tk.Frame(window, bg=COLORS["bg_primary"])
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Camera index
        camera_frame = tk.Frame(content, bg=COLORS["bg_secondary"], relief=tk.FLAT)
        camera_frame.pack(pady=15, padx=0, fill=tk.X)
        
        tk.Label(
            camera_frame,
            text="Camera Index",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(anchor=tk.W, padx=20, pady=(15, 5))
        
        spinbox_frame = tk.Frame(camera_frame, bg=COLORS["bg_secondary"])
        spinbox_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        tk.Label(
            spinbox_frame,
            text="Device:",
            font=("Segoe UI", 10),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_secondary"]
        ).pack(side=tk.LEFT)
        
        camera_spinbox = tk.Spinbox(
            spinbox_frame,
            from_=0,
            to=5,
            textvariable=self.camera_index,
            width=10,
            font=("Segoe UI", 10),
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            buttonbackground=COLORS["accent_blue"],
            relief=tk.FLAT
        )
        camera_spinbox.pack(side=tk.RIGHT)
        
        # Model type
        model_frame = tk.Frame(content, bg=COLORS["bg_secondary"], relief=tk.FLAT)
        model_frame.pack(pady=15, padx=0, fill=tk.X)
        
        tk.Label(
            model_frame,
            text="🤖 Detection Model:",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(anchor=tk.W, padx=20, pady=(15, 10))
        
        radio_frame = tk.Frame(model_frame, bg=COLORS["bg_secondary"])
        radio_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        tk.Radiobutton(
            radio_frame,
            text="HOG (CPU - Faster)",
            variable=self.model_type,
            value="hog",
            font=("Segoe UI", 10),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"],
            selectcolor=COLORS["bg_tertiary"],
            activebackground=COLORS["bg_secondary"],
            activeforeground=COLORS["text_primary"]
        ).pack(anchor=tk.W, padx=10)
        
        tk.Radiobutton(
            radio_frame,
            text="CNN (GPU - More Accurate)",
            variable=self.model_type,
            value="cnn",
            font=("Segoe UI", 10),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"],
            selectcolor=COLORS["bg_tertiary"],
            activebackground=COLORS["bg_secondary"],
            activeforeground=COLORS["text_primary"]
        ).pack(anchor=tk.W, padx=10)
        
        # Gemini API Key Section (More Prominent)
        gemini_header_frame = tk.Frame(content, bg=COLORS["accent_blue"], relief=tk.FLAT)
        gemini_header_frame.pack(pady=15, padx=0, fill=tk.X)
        
        tk.Label(
            gemini_header_frame,
            text="🤖 Gemini API Key (For Live Voice Calls)",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["accent_blue"],
            fg=COLORS["text_primary"],
            pady=10
        ).pack(anchor=tk.W, padx=15)
        
        gemini_frame = tk.Frame(content, bg=COLORS["bg_secondary"], relief=tk.FLAT)
        gemini_frame.pack(padx=0, fill=tk.X)
        
        tk.Label(
            gemini_frame,
            text="Enter your Google Gemini API key to enable live voice calls:",
            font=("Segoe UI", 9),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_secondary"]
        ).pack(anchor=tk.W, padx=20, pady=(15, 5))
        
        tk.Label(
            gemini_frame,
            text="Get your free API key from: https://makersuite.google.com/app/apikey",
            font=("Segoe UI", 8),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_secondary"],
            cursor="hand2"
        ).pack(anchor=tk.W, padx=20, pady=(0, 10))
        
        # API Key Entry (More Visible)
        entry_frame = tk.Frame(gemini_frame, bg=COLORS["bg_secondary"])
        entry_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        tk.Label(
            entry_frame,
            text="API Key:",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        gemini_entry = tk.Entry(
            entry_frame,
            textvariable=self.gemini_api_key,
            font=("Segoe UI", 11),
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief=tk.FLAT,
            show="*",  # Hide API key
            width=45
        )
        gemini_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Show/Hide toggle button
        def toggle_show_key():
            if gemini_entry.cget("show") == "*":
                gemini_entry.config(show="")
                show_btn.config(text="👁️ Hide")
            else:
                gemini_entry.config(show="*")
                show_btn.config(text="👁️ Show")
        
        show_btn = tk.Button(
            entry_frame,
            text="👁️ Show",
            command=toggle_show_key,
            font=("Segoe UI", 8),
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            relief=tk.FLAT,
            padx=8,
            pady=2
        )
        show_btn.pack(side=tk.LEFT)
        
        # API Key Status
        api_key_status_text = "✓ API key is set" if self.gemini_api_key.get().strip() else "⚠️ API key not set"
        api_key_status_color = COLORS["success"] if self.gemini_api_key.get().strip() else COLORS["warning"]
        
        status_label = tk.Label(
            gemini_frame,
            text=api_key_status_text,
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["bg_secondary"],
            fg=api_key_status_color
        )
        status_label.pack(anchor=tk.W, padx=20, pady=(0, 15))
        
        # Update status when entry changes and auto-save
        def update_status(*args):
            api_key_status_text = "✓ API key is set" if self.gemini_api_key.get().strip() else "⚠️ API key not set"
            api_key_status_color = COLORS["success"] if self.gemini_api_key.get().strip() else COLORS["warning"]
            status_label.config(text=api_key_status_text, fg=api_key_status_color)
            
            # Auto-save when API key changes (with small delay to avoid too many saves)
            if hasattr(self, '_save_timer'):
                try:
                    self.root.after_cancel(self._save_timer)
                except:
                    pass
            # Only auto-save if key is not empty (to avoid clearing on startup)
            if self.gemini_api_key.get().strip():
                self._save_timer = self.root.after(500, lambda: self.save_gemini_api_key())  # Save 500ms after last change
        
        # Trace the variable to auto-save on changes
        self.gemini_api_key.trace("w", update_status)
        
        close_btn = tk.Button(
            content,
            text="💾 Save & Close",
            command=lambda: self.save_settings(window),
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        )
        close_btn.pack(pady=20)
    
    def save_settings(self, window):
        """Save settings and close window."""
        # Always save Gemini API key when Settings closes (explicit save)
        print("=" * 50)
        print("Saving API key from Settings window...")
        saved = self.save_gemini_api_key()
        print("=" * 50)
        
        if saved:
            window.destroy()
            messagebox.showinfo(
                "Success", 
                "Settings saved successfully!\n\n"
                "API key has been saved and will persist when you restart the app.\n\n"
                f"File location: output/gemini_api_key.txt"
            )
        else:
            # Still close but warn user
            response = messagebox.askyesno(
                "Save Warning",
                "There was an issue saving the API key.\n\n"
                "Do you want to close anyway?\n"
                "(You can try saving again later)"
            )
            if response:
                window.destroy()


def main():
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    
    # Save API key when app closes
    def on_closing():
        # Save API key before closing (always save, even if empty)
        print("Saving API key before app closes...")
        try:
            app.save_gemini_api_key()
            print("✓ API key saved on app close")
        except Exception as e:
            print(f"⚠️ Error saving API key on close: {e}")
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
