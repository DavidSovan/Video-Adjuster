import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import threading
from pathlib import Path
import json
import time
from tkinterdnd2 import DND_FILES, TkinterDnD
import re

class VideoSpeedupTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Speed-Up Tool")
        self.root.geometry("800x700")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.video_files = []
        self.output_folder = tk.StringVar()
        self.processing = False
        self.supported_formats = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        
        # Check FFmpeg availability and hardware acceleration
        self.ffmpeg_available = self.check_ffmpeg()
        self.hw_acceleration = self.detect_hardware_acceleration()
        
        self.setup_ui()
        self.setup_drag_drop()
        
    def detect_hardware_acceleration(self):
        """Detect available hardware acceleration options"""
        if not self.ffmpeg_available:
            return {'available': [], 'selected': 'cpu'}
            
        hw_options = []
        
    def check_ffmpeg(self):
        """Check if FFmpeg is available"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
            
    def detect_hardware_acceleration(self):
        """Detect available hardware acceleration options"""
        if not self.ffmpeg_available:
            return {'available': [], 'selected': 'cpu'}
            
        hw_options = []
        
        # Test for NVIDIA GPU (NVENC)
        try:
            result = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], 
                                  capture_output=True, text=True, check=True)
            if 'h264_nvenc' in result.stdout:
                hw_options.append('nvenc')
        except:
            pass
            
        # Test for AMD GPU (AMF)
        try:
            result = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], 
                                  capture_output=True, text=True, check=True)
            if 'h264_amf' in result.stdout:
                hw_options.append('amf')
        except:
            pass
            
        # Test for Intel GPU (QuickSync)
        try:
            result = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], 
                                  capture_output=True, text=True, check=True)
            if 'h264_qsv' in result.stdout:
                hw_options.append('qsv')
        except:
            pass
            
        # Test for Apple VideoToolbox (macOS)
        try:
            result = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], 
                                  capture_output=True, text=True, check=True)
            if 'h264_videotoolbox' in result.stdout:
                hw_options.append('videotoolbox')
        except:
            pass
            
        # Test for VAAPI (Linux)
        try:
            result = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], 
                                  capture_output=True, text=True, check=True)
            if 'h264_vaapi' in result.stdout:
                hw_options.append('vaapi')
        except:
            pass
            
        return {
            'available': hw_options,
            'selected': hw_options[0] if hw_options else 'cpu'
        }
    
    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Video Speed-Up Tool", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # FFmpeg and Hardware status
        status_row = 1
        if not self.ffmpeg_available:
            warning_label = ttk.Label(main_frame, 
                                    text="⚠️ FFmpeg not found! Please install FFmpeg to use this tool.",
                                    foreground='red', font=('Arial', 10, 'bold'))
            warning_label.grid(row=status_row, column=0, columnspan=3, pady=(0, 10))
            status_row += 1
        
        # Hardware acceleration status
        if self.hw_acceleration['available']:
            hw_status = f"🚀 Hardware Acceleration: {', '.join(self.hw_acceleration['available']).upper()}"
            hw_color = 'green'
        else:
            hw_status = "⚡ CPU Processing Only"
            hw_color = 'orange'
            
        hw_label = ttk.Label(main_frame, text=hw_status, foreground=hw_color, 
                            font=('Arial', 10, 'bold'))
        hw_label.grid(row=status_row, column=0, columnspan=3, pady=(0, 10))
        status_row += 1
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="Video Files", padding="10")
        file_frame.grid(row=status_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_row += 1
        
        # Drag and drop area
        self.drop_label = ttk.Label(file_frame, 
                                   text="Drag & Drop video files or folders here\n(or use buttons below)",
                                   background='white', relief='sunken', padding="20")
        self.drop_label.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # File operation buttons
        btn_frame = ttk.Frame(file_frame)
        btn_frame.grid(row=1, column=0, columnspan=3, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Add Video Files", 
                  command=self.add_video_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Add Folder", 
                  command=self.add_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear All", 
                  command=self.clear_files).pack(side=tk.LEFT, padx=5)
        
        # File list
        list_frame = ttk.Frame(file_frame)
        list_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Treeview for file list with individual settings
        self.file_tree = ttk.Treeview(list_frame, columns=('speed', 'fps', 'quality'), 
                                     show='tree headings', height=8)
        self.file_tree.heading('#0', text='Video File')
        self.file_tree.heading('speed', text='Speed (x)')
        self.file_tree.heading('fps', text='Frame Rate')
        self.file_tree.heading('quality', text='Quality')
        
        self.file_tree.column('#0', width=300)
        self.file_tree.column('speed', width=100)
        self.file_tree.column('fps', width=100)
        self.file_tree.column('quality', width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind double-click to edit settings
        self.file_tree.bind('<Double-1>', self.edit_video_settings)
        
        # Global settings section
        settings_frame = ttk.LabelFrame(main_frame, text="Global Settings", padding="10")
        settings_frame.grid(row=status_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_row += 1
        
        # Speed setting
        ttk.Label(settings_frame, text="Default Speed Multiplier:").grid(row=0, column=0, sticky=tk.W)
        self.speed_var = tk.StringVar(value="2.0")
        speed_entry = ttk.Entry(settings_frame, textvariable=self.speed_var, width=10)
        speed_entry.grid(row=0, column=1, padx=(5, 20), sticky=tk.W)
        
        # Frame rate setting
        ttk.Label(settings_frame, text="Frame Rate:").grid(row=0, column=2, sticky=tk.W)
        self.fps_var = tk.StringVar(value="30")
        fps_combo = ttk.Combobox(settings_frame, textvariable=self.fps_var, 
                                values=["30", "60", "Keep Original"], width=12)
        fps_combo.grid(row=0, column=3, padx=(5, 20), sticky=tk.W)
        
        # Quality setting
        ttk.Label(settings_frame, text="Quality:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.quality_var = tk.StringVar(value="High")
        quality_combo = ttk.Combobox(settings_frame, textvariable=self.quality_var,
                                   values=["Low", "Medium", "High", "Very High"], width=12)
        quality_combo.grid(row=1, column=1, padx=(5, 20), sticky=tk.W, pady=(10, 0))
        
        # Apply to all button
        ttk.Button(settings_frame, text="Apply to All Videos", 
                  command=self.apply_to_all).grid(row=1, column=2, columnspan=2, 
                                                padx=(20, 0), pady=(10, 0))
        
        # Performance settings
        ttk.Label(settings_frame, text="Hardware Acceleration:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.hw_accel_var = tk.StringVar(value=self.hw_acceleration['selected'])
        hw_options = ['cpu'] + self.hw_acceleration['available']
        hw_combo = ttk.Combobox(settings_frame, textvariable=self.hw_accel_var, 
                               values=hw_options, width=12)
        hw_combo.grid(row=2, column=1, padx=(5, 20), sticky=tk.W, pady=(10, 0))
        
        # CPU threads
        ttk.Label(settings_frame, text="CPU Threads:").grid(row=2, column=2, sticky=tk.W, pady=(10, 0))
        self.threads_var = tk.StringVar(value="auto")
        threads_combo = ttk.Combobox(settings_frame, textvariable=self.threads_var,
                                   values=["auto", "1", "2", "4", "6", "8", "12", "16"], width=8)
        threads_combo.grid(row=2, column=3, padx=(5, 0), sticky=tk.W, pady=(10, 0))
        
        # Output folder section
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="10")
        output_frame.grid(row=status_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_row += 1
        
        ttk.Label(output_frame, text="Output Folder:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(output_frame, textvariable=self.output_folder, width=50).grid(row=0, column=1, 
                                                                               padx=(5, 5), sticky=(tk.W, tk.E))
        ttk.Button(output_frame, text="Browse", 
                  command=self.select_output_folder).grid(row=0, column=2)
        
        # Preview section
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="10")
        preview_frame.grid(row=status_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_row += 1
        
        ttk.Button(preview_frame, text="Preview Selected Video (10 seconds)", 
                  command=self.preview_video).pack(side=tk.LEFT, padx=(0, 10))
        
        self.preview_label = ttk.Label(preview_frame, text="Select a video to preview")
        self.preview_label.pack(side=tk.LEFT)
        
        # Processing section
        process_frame = ttk.LabelFrame(main_frame, text="Processing", padding="10")
        process_frame.grid(row=status_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready to process videos")
        ttk.Label(process_frame, textvariable=self.progress_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(process_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 10))
        
        # Process button
        self.process_btn = ttk.Button(process_frame, text="Start Processing", 
                                     command=self.start_processing)
        self.process_btn.grid(row=2, column=0, pady=(0, 5))
        
        self.stop_btn = ttk.Button(process_frame, text="Stop Processing", 
                                  command=self.stop_processing, state='disabled')
        self.stop_btn.grid(row=2, column=1, padx=(10, 0), pady=(0, 5))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        file_frame.columnconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(1, weight=1)
        process_frame.columnconfigure(0, weight=1)
        
    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.handle_drop)
        
    def handle_drop(self, event):
        """Handle dropped files/folders"""
        files = self.root.tk.splitlist(event.data)
        for file_path in files:
            if os.path.isfile(file_path):
                if Path(file_path).suffix.lower() in self.supported_formats:
                    self.add_video_to_list(file_path)
            elif os.path.isdir(file_path):
                self.add_videos_from_folder(file_path)
        self.update_file_list()
        
    def add_video_files(self):
        """Add individual video files"""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v"),
            ("All files", "*.*")
        ]
        files = filedialog.askopenfilenames(title="Select Video Files", filetypes=filetypes)
        for file_path in files:
            self.add_video_to_list(file_path)
        self.update_file_list()
        
    def add_folder(self):
        """Add all videos from a folder"""
        folder_path = filedialog.askdirectory(title="Select Folder with Videos")
        if folder_path:
            self.add_videos_from_folder(folder_path)
            self.update_file_list()
            
    def add_videos_from_folder(self, folder_path):
        """Add all supported video files from a folder"""
        for file_path in Path(folder_path).rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                self.add_video_to_list(str(file_path))
                
    def add_video_to_list(self, file_path):
        """Add a video file to the processing list"""
        if file_path not in [video['path'] for video in self.video_files]:
            video_info = {
                'path': file_path,
                'speed': float(self.speed_var.get()),
                'fps': self.fps_var.get(),
                'quality': self.quality_var.get()
            }
            self.video_files.append(video_info)
            
    def update_file_list(self):
        """Update the file list display"""
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
            
        # Add videos to tree
        for video in self.video_files:
            filename = Path(video['path']).name
            self.file_tree.insert('', 'end', text=filename, 
                                values=(video['speed'], video['fps'], video['quality']))
                                
    def edit_video_settings(self, event):
        """Edit settings for selected video"""
        selection = self.file_tree.selection()
        if not selection:
            return
            
        item_id = selection[0]
        item_index = self.file_tree.index(item_id)
        video = self.video_files[item_index]
        
        # Create settings dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Video Settings")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Settings fields
        ttk.Label(dialog, text="Speed Multiplier:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        speed_var = tk.StringVar(value=str(video['speed']))
        ttk.Entry(dialog, textvariable=speed_var).grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Frame Rate:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        fps_var = tk.StringVar(value=video['fps'])
        ttk.Combobox(dialog, textvariable=fps_var, 
                    values=["30", "60", "Keep Original"]).grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Quality:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        quality_var = tk.StringVar(value=video['quality'])
        ttk.Combobox(dialog, textvariable=quality_var,
                    values=["Low", "Medium", "High", "Very High"]).grid(row=2, column=1, padx=10, pady=5)
        
        def save_settings():
            try:
                video['speed'] = float(speed_var.get())
                video['fps'] = fps_var.get()
                video['quality'] = quality_var.get()
                self.update_file_list()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid speed value!")
                
        ttk.Button(dialog, text="Save", command=save_settings).grid(row=3, column=0, pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=3, column=1, pady=20)
        
    def apply_to_all(self):
        """Apply current global settings to all videos"""
        try:
            speed = float(self.speed_var.get())
            fps = self.fps_var.get()
            quality = self.quality_var.get()
            
            for video in self.video_files:
                video['speed'] = speed
                video['fps'] = fps
                video['quality'] = quality
                
            self.update_file_list()
            messagebox.showinfo("Success", "Settings applied to all videos!")
        except ValueError:
            messagebox.showerror("Error", "Invalid speed value!")
            
    def clear_files(self):
        """Clear all video files from the list"""
        self.video_files.clear()
        self.update_file_list()
        
    def select_output_folder(self):
        """Select output folder"""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
            
    def preview_video(self):
        """Preview selected video with current settings"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a video to preview!")
            return
            
        if not self.ffmpeg_available:
            messagebox.showerror("Error", "FFmpeg is required for preview functionality!")
            return
            
        item_index = self.file_tree.index(selection[0])
        video = self.video_files[item_index]
        
        # Create preview in temp folder
        temp_dir = Path.home() / "temp_video_preview"
        temp_dir.mkdir(exist_ok=True)
        
        input_path = video['path']
        preview_path = temp_dir / f"preview_{Path(input_path).stem}.mp4"
        
        # Build FFmpeg command for 10-second preview
        cmd = self.build_ffmpeg_command(input_path, str(preview_path), video, preview=True)
        
        def run_preview():
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                self.preview_label.config(text=f"Preview saved: {preview_path}")
                
                # Try to open the preview
                if os.name == 'nt':  # Windows
                    os.startfile(str(preview_path))
                elif os.name == 'posix':  # macOS and Linux
                    os.system(f'open "{preview_path}"' if os.uname().sysname == 'Darwin' 
                             else f'xdg-open "{preview_path}"')
                             
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Preview Error", f"Failed to create preview: {e}")
                
        threading.Thread(target=run_preview, daemon=True).start()
        
    def build_ffmpeg_command(self, input_path, output_path, video_settings, preview=False):
        """Build FFmpeg command based on settings with hardware acceleration"""
        cmd = ['ffmpeg', '-i', input_path]
        
        # Hardware acceleration setup
        hw_accel = self.hw_accel_var.get() if hasattr(self, 'hw_accel_var') else 'cpu'
        
        # Add hardware decoding if available
        if hw_accel != 'cpu':
            if hw_accel == 'nvenc':
                cmd.extend(['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda'])
            elif hw_accel == 'qsv':
                cmd.extend(['-hwaccel', 'qsv', '-hwaccel_output_format', 'qsv'])
            elif hw_accel == 'vaapi':
                cmd.extend(['-hwaccel', 'vaapi', '-vaapi_device', '/dev/dri/renderD128'])
            elif hw_accel == 'videotoolbox':
                cmd.extend(['-hwaccel', 'videotoolbox'])
        
        # CPU threads optimization
        threads = self.threads_var.get() if hasattr(self, 'threads_var') else 'auto'
        if threads != 'auto':
            cmd.extend(['-threads', threads])
        
        # Preview mode - only first 10 seconds
        if preview:
            cmd.extend(['-t', '10'])
            
        # Speed and filter settings
        speed = video_settings['speed']
        
        # Hardware-accelerated filters when possible
        if hw_accel == 'nvenc' and not preview:
            # Use CUDA filters for NVIDIA
            video_filter = f"setpts={1/speed}*PTS"
        elif hw_accel == 'qsv' and not preview:
            # Use QuickSync filters for Intel
            video_filter = f"setpts={1/speed}*PTS"
        else:
            # Standard CPU filters
            video_filter = f"setpts={1/speed}*PTS"
        
        # Audio filter (always CPU-based)
        audio_filter = f"atempo={min(speed, 2.0)}"
        
        # Handle speeds > 2.0 for audio
        if speed > 2.0:
            remaining_speed = speed / 2.0
            while remaining_speed > 2.0:
                audio_filter += f",atempo=2.0"
                remaining_speed /= 2.0
            if remaining_speed > 1.0:
                audio_filter += f",atempo={remaining_speed}"
                
        # Apply filters
        cmd.extend(['-filter:v', video_filter, '-filter:a', audio_filter])
        
        # Frame rate
        if video_settings['fps'] != "Keep Original":
            cmd.extend(['-r', video_settings['fps']])
            
        # Hardware encoder selection and quality
        if hw_accel == 'nvenc':
            cmd.extend(['-c:v', 'h264_nvenc'])
            # NVENC quality mapping
            quality_map = {
                "Low": ['-preset', 'fast', '-cq', '30'],
                "Medium": ['-preset', 'medium', '-cq', '25'],
                "High": ['-preset', 'slow', '-cq', '20'],
                "Very High": ['-preset', 'slow', '-cq', '18']
            }
        elif hw_accel == 'amf':
            cmd.extend(['-c:v', 'h264_amf'])
            # AMF quality mapping
            quality_map = {
                "Low": ['-quality', 'speed', '-qp_i', '30'],
                "Medium": ['-quality', 'balanced', '-qp_i', '25'],
                "High": ['-quality', 'quality', '-qp_i', '20'],
                "Very High": ['-quality', 'quality', '-qp_i', '18']
            }
        elif hw_accel == 'qsv':
            cmd.extend(['-c:v', 'h264_qsv'])
            # QuickSync quality mapping
            quality_map = {
                "Low": ['-preset', 'veryfast', '-global_quality', '30', '-look_ahead', '0'],
                "Medium": ['-preset', 'medium', '-global_quality', '25', '-look_ahead', '1'],
                "High": ['-preset', 'slow', '-global_quality', '20', '-look_ahead', '1'],
                "Very High": ['-preset', 'slower', '-global_quality', '18', '-look_ahead', '1']
            }
        elif hw_accel == 'videotoolbox':
            cmd.extend(['-c:v', 'h264_videotoolbox'])
            # VideoToolbox quality mapping
            quality_map = {
                "Low": ['-q:v', '60'],
                "Medium": ['-q:v', '50'],
                "High": ['-q:v', '40'],
                "Very High": ['-q:v', '30']
            }
        elif hw_accel == 'vaapi':
            cmd.extend(['-c:v', 'h264_vaapi'])
            # VAAPI quality mapping
            quality_map = {
                "Low": ['-qp', '30'],
                "Medium": ['-qp', '25'],
                "High": ['-qp', '20'],
                "Very High": ['-qp', '18']
            }
        else:
            # CPU encoding (libx264)
            cmd.extend(['-c:v', 'libx264'])
            # Standard quality mapping
            quality_map = {
                "Low": ['-crf', '28', '-preset', 'ultrafast'],
                "Medium": ['-crf', '23', '-preset', 'fast'],
                "High": ['-crf', '18', '-preset', 'medium'],
                "Very High": ['-crf', '15', '-preset', 'slow']
            }
        
        # Apply quality settings
        cmd.extend(quality_map[video_settings['quality']])
        
        # Audio encoding
        cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
        
        # Output optimization
        cmd.extend(['-movflags', '+faststart'])  # Web optimization
        
        # Overwrite output
        cmd.extend(['-y', output_path])
        
        return cmd
        
    def generate_output_filename(self, input_path, speed, output_folder):
        """Generate output filename with conflict resolution"""
        input_file = Path(input_path)
        base_name = input_file.stem
        extension = input_file.suffix
        
        # Create base output filename
        output_name = f"{base_name}_{speed}x{extension}"
        output_path = Path(output_folder) / output_name
        
        # Handle conflicts
        counter = 1
        while output_path.exists():
            output_name = f"{base_name}_{speed}x_{counter}{extension}"
            output_path = Path(output_folder) / output_name
            counter += 1
            
        return str(output_path)
        
    def start_processing(self):
        """Start processing all videos"""
        if not self.video_files:
            messagebox.showwarning("Warning", "No video files selected!")
            return
            
        if not self.output_folder.get():
            messagebox.showwarning("Warning", "Please select an output folder!")
            return
            
        if not self.ffmpeg_available:
            messagebox.showerror("Error", "FFmpeg is required for video processing!")
            return
            
        # Create output folder if it doesn't exist
        output_dir = Path(self.output_folder.get())
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.processing = True
        self.process_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # Start processing in separate thread
        threading.Thread(target=self.process_videos, daemon=True).start()
        
    def process_videos(self):
        """Process all videos"""
        total_videos = len(self.video_files)
        
        for i, video in enumerate(self.video_files):
            if not self.processing:  # Check if stopped
                break
                
            # Update progress
            self.root.after(0, lambda v=video, i=i, t=total_videos: 
                          self.update_progress(f"Processing {Path(v['path']).name} ({i+1}/{t})", 
                                             (i/t)*100))
            
            try:
                # Generate output filename
                output_path = self.generate_output_filename(
                    video['path'], video['speed'], self.output_folder.get()
                )
                
                # Build and execute FFmpeg command
                cmd = self.build_ffmpeg_command(video['path'], output_path, video)
                subprocess.run(cmd, check=True, capture_output=True)
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to process {Path(video['path']).name}: {e}"
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Processing Error", msg))
                
        # Processing complete
        if self.processing:
            self.root.after(0, lambda: self.update_progress("Processing complete!", 100))
            self.root.after(0, lambda: messagebox.showinfo("Success", 
                          f"Successfully processed {total_videos} video(s)!"))
        else:
            self.root.after(0, lambda: self.update_progress("Processing stopped by user", 0))
            
        self.root.after(0, self.reset_ui)
        
    def update_progress(self, message, percentage):
        """Update progress bar and message"""
        self.progress_var.set(message)
        self.progress_bar.config(value=percentage)
        
    def stop_processing(self):
        """Stop the processing"""
        self.processing = False
        
    def reset_ui(self):
        """Reset UI after processing"""
        self.processing = False
        self.process_btn.config(state='normal')
        self.stop_btn.config(state='disabled')


def main():
    try:
        # Try to use TkinterDnD for drag and drop
        root = TkinterDnD.Tk()
    except:
        # Fallback to regular tkinter if TkinterDnD is not available
        root = tk.Tk()
        messagebox.showwarning("Warning", 
                             "Drag and drop functionality requires tkinterdnd2 package.\n"
                             "Install with: pip install tkinterdnd2")
    
    app = VideoSpeedupTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()