import sys
import os
import re
import json
import subprocess

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup,
    QCheckBox, QProgressBar, QTextEdit, QFileDialog,
    QGroupBox, QFrame, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont

from ui.styles import DARK_NEON_STYLE
from downloader import DownloadWorker


# --- ANSI ESCAPE CODE STRIPPER ---
def clean_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


SETTINGS_FILE = "settings.json"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = self.load_settings()
        self.worker = None

        self.setWindowTitle("Music Auto Downloader PRO - Yashvir Gaming")
        self.resize(900, 650)
        self.setup_ui()
        self.setStyleSheet(DARK_NEON_STYLE)
        self.load_settings_to_ui()

        # ---------------------------------------------------------
        # ICON SETUP FOR PYSIDE6 WINDOW
        # ---------------------------------------------------------
        if getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS'):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            icon_path = os.path.join(base_dir, "icons", "icon.ico")
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_dir, "icons", "icon.ico")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["artists"] = []
                    return data
            except Exception:
                pass
        return {
            "artists": [],
            "limit": 10,
            "output_dir": os.path.join(os.path.expanduser("~"), "Music", "Car Audio"),
            "download_mp3": True,
            "skip_shorts": True,
            "skip_downloaded": True,
            "official_only": True,
            "embed_thumbnail": True,
            "add_metadata": True,
            "bitrate": "128",
            "antiban": True
        }

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header_box = QVBoxLayout()
        title_label = QLabel("🎵 Music Auto Downloader PRO")
        title_font = QFont("Segoe UI")
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        
        subtitle_label = QLabel("by Yashvir Gaming")
        sub_font = QFont("Segoe UI")
        sub_font.setPointSize(10)
        sub_font.setBold(True)
        subtitle_label.setFont(sub_font)
        subtitle_label.setStyleSheet("color: #00e5ff;")
        subtitle_label.setAlignment(Qt.AlignCenter)

        header_box.addWidget(title_label)
        header_box.addWidget(subtitle_label)
        main_layout.addLayout(header_box)

        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        main_layout.addWidget(line1)

        # Multi-line Text Box
        artist_group = QGroupBox("Artists / Specific Song Links / Search Queries")
        artist_layout = QVBoxLayout(artist_group)
        
        self.artist_input_box = QTextEdit()
        self.artist_input_box.setPlaceholderText("Paste URLs or search queries directly here (one per line)...")
        self.artist_input_box.setFixedHeight(120)
        artist_layout.addWidget(self.artist_input_box)

        artist_input_layout = QHBoxLayout()
        self.btn_import_txt = QPushButton("Import TXT")
        self.btn_clear_input = QPushButton("Clear All")

        artist_input_layout.addWidget(self.btn_import_txt)
        artist_input_layout.addWidget(self.btn_clear_input)
        artist_layout.addLayout(artist_input_layout)
        main_layout.addWidget(artist_group)

        # Bitrate Quality Selector
        audio_group = QGroupBox("Audio Bitrate Settings")
        audio_layout = QVBoxLayout(audio_group)

        bitrate_row = QHBoxLayout()
        bitrate_row.addWidget(QLabel("Bitrate Quality:"))
        self.combo_bitrate = QComboBox()
        self.combo_bitrate.addItems(["128 kbps (Max Stereo Compatibility)", "192 kbps (Standard)", "320 kbps (High Quality)"])
        bitrate_row.addWidget(self.combo_bitrate)
        audio_layout.addLayout(bitrate_row)

        lbl_warning = QLabel("⚠️ Note: Older car head-units / USB players might not decode 320kbps VBR MP3 files. Use 128kbps for max compatibility.")
        lbl_warning.setWordWrap(True)
        lbl_warning.setStyleSheet("color: #ffb74d; font-size: 11px;")
        audio_layout.addWidget(lbl_warning)

        main_layout.addWidget(audio_group)

        # Anti-Ban Protection
        antiban_group = QGroupBox("Anti-Ban / Rate-Limit Protection")
        antiban_layout = QVBoxLayout(antiban_group)
        
        self.chk_antiban = QCheckBox("Enable Anti-Ban Safe Delays (Recommended)")
        self.chk_antiban.setChecked(True)
        antiban_layout.addWidget(self.chk_antiban)

        lbl_ab_warning = QLabel("🛡️ Prevents YouTube IP bans/captchas by adding random delays (3-7s) between bulk downloads.")
        lbl_ab_warning.setWordWrap(True)
        lbl_ab_warning.setStyleSheet("color: #81c784; font-size: 11px;")
        antiban_layout.addWidget(lbl_ab_warning)

        main_layout.addWidget(antiban_group)

        # Limits Box
        limit_group = QGroupBox("Latest Songs per Artist")
        limit_layout = QHBoxLayout(limit_group)
        self.limit_button_group = QButtonGroup(self)

        for val in [5, 10, 20, 50]:
            rb = QRadioButton(str(val))
            limit_layout.addWidget(rb)
            self.limit_button_group.addButton(rb, val)

        main_layout.addWidget(limit_group)

        # Output Folder Box
        folder_group = QGroupBox("Output Folder")
        folder_layout = QHBoxLayout(folder_group)
        self.folder_input = QLineEdit()
        self.folder_input.setReadOnly(True)
        self.btn_browse = QPushButton("Browse...")
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.btn_browse)
        main_layout.addWidget(folder_group)

        # Options Box
        opts_group = QGroupBox("Options")
        opts_layout = QVBoxLayout(opts_group)

        self.chk_mp3 = QCheckBox("Download as MP3")
        self.chk_shorts = QCheckBox("Skip Shorts")
        self.chk_skip_dl = QCheckBox("Skip already downloaded songs")
        self.chk_official = QCheckBox("Only Official Artist Channels")
        self.chk_thumb = QCheckBox("Embed Thumbnail")
        self.chk_metadata = QCheckBox("Add Artist Metadata")

        for chk in [self.chk_mp3, self.chk_shorts, self.chk_skip_dl,
                    self.chk_official, self.chk_thumb, self.chk_metadata]:
            opts_layout.addWidget(chk)
        main_layout.addWidget(opts_group)

        # Progress Indicators
        progress_box = QVBoxLayout()
        self.lbl_current_artist = QLabel("Current Artist: —")
        self.lbl_current_song = QLabel("Current Song: —")
        self.progress_bar = QProgressBar()

        progress_box.addWidget(self.lbl_current_artist)
        progress_box.addWidget(self.lbl_current_song)
        progress_box.addWidget(self.progress_bar)
        main_layout.addLayout(progress_box)

        # Controls
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("START")
        self.btn_start.setObjectName("btnStart")
        
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setEnabled(False)

        self.btn_open_folder = QPushButton("📁 Open Output Folder")
        self.btn_open_folder.setStyleSheet("font-weight: bold;")

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addWidget(self.btn_open_folder)
        main_layout.addLayout(btn_layout)

        # Log Output
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setFixedHeight(90)
        main_layout.addWidget(self.log_console)

        # Footer
        footer_label = QLabel("Made with ❤️ by Yashvir Gaming")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #7b849b; font-size: 11px;")
        main_layout.addWidget(footer_label)

        # Signals
        self.btn_import_txt.clicked.connect(self.import_artists)
        self.btn_clear_input.clicked.connect(self.clear_input_box)
        self.btn_browse.clicked.connect(self.browse_folder)
        self.btn_open_folder.clicked.connect(self.open_output_folder)
        self.btn_start.clicked.connect(self.start_download)
        self.btn_stop.clicked.connect(self.stop_download)

    def load_settings_to_ui(self):
        artists = self.settings.get("artists", [])
        self.artist_input_box.setPlainText("\n".join(artists))

        limit_val = self.settings.get("limit", 10)
        for rb in self.limit_button_group.buttons():
            if int(rb.text()) == limit_val:
                rb.setChecked(True)

        bitrate = self.settings.get("bitrate", "128")
        if bitrate == "128":
            self.combo_bitrate.setCurrentIndex(0)
        elif bitrate == "192":
            self.combo_bitrate.setCurrentIndex(1)
        else:
            self.combo_bitrate.setCurrentIndex(2)

        self.chk_antiban.setChecked(self.settings.get("antiban", True))
        self.folder_input.setText(self.settings.get("output_dir", ""))
        self.chk_mp3.setChecked(self.settings.get("download_mp3", True))
        self.chk_shorts.setChecked(self.settings.get("skip_shorts", True))
        self.chk_skip_dl.setChecked(self.settings.get("skip_downloaded", True))
        self.chk_official.setChecked(self.settings.get("official_only", True))
        self.chk_thumb.setChecked(self.settings.get("embed_thumbnail", True))
        self.chk_metadata.setChecked(self.settings.get("add_metadata", True))

    def update_settings_from_ui(self):
        raw_text = self.artist_input_box.toPlainText()
        self.settings["artists"] = [line.strip() for line in raw_text.splitlines() if line.strip()]
        
        self.settings["limit"] = self.limit_button_group.checkedId()
        
        selected_b = self.combo_bitrate.currentIndex()
        self.settings["bitrate"] = "128" if selected_b == 0 else ("192" if selected_b == 1 else "320")
        
        self.settings["antiban"] = self.chk_antiban.isChecked()
        self.settings["output_dir"] = self.folder_input.text()
        self.settings["download_mp3"] = self.chk_mp3.isChecked()
        self.settings["skip_shorts"] = self.chk_shorts.isChecked()
        self.settings["skip_downloaded"] = self.chk_skip_dl.isChecked()
        self.settings["official_only"] = self.chk_official.isChecked()
        self.settings["embed_thumbnail"] = self.chk_thumb.isChecked()
        self.settings["add_metadata"] = self.chk_metadata.isChecked()
        self.save_settings()

    def clear_input_box(self):
        self.artist_input_box.clear()
        self.update_settings_from_ui()

    def import_artists(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Artists List", "", "Text Files (*.txt)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    current_text = self.artist_input_box.toPlainText().strip()
                    if current_text:
                        self.artist_input_box.setPlainText(current_text + "\n" + content)
                    else:
                        self.artist_input_box.setPlainText(content)
                self.update_settings_from_ui()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import: {e}")

    def browse_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory", self.folder_input.text())
        if dir_path:
            self.folder_input.setText(dir_path)
            self.update_settings_from_ui()

    def open_output_folder(self):
        folder_path = self.folder_input.text()
        if not folder_path or not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
            
        try:
            if sys.platform == 'win32':
                os.startfile(folder_path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', folder_path])
            else:
                subprocess.Popen(['xdg-open', folder_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open folder: {e}")

    def append_log(self, message):
        cleaned_text = clean_ansi(message)
        self.log_console.append(cleaned_text)

    def start_download(self):
        self.update_settings_from_ui()
        if not self.settings.get("artists"):
            QMessageBox.warning(self, "Warning", "Paste at least one artist, song name, or link to download.")
            return

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.log_console.clear()

        self.worker = DownloadWorker(self.settings)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.log_signal.connect(self.append_log)  
        self.worker.finished_signal.connect(self.download_finished)
        self.worker.start()

    def stop_download(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.log_console.append("🛑 Cancelling tasks...")

    def update_progress(self, data):
        self.lbl_current_artist.setText(f"Current Target: {data.get('artist', '')}")
        self.lbl_current_song.setText(f"Current Song: {data.get('song', '')}")
        self.progress_bar.setValue(data.get('overall_percent', 0))

    def download_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.open_output_folder()