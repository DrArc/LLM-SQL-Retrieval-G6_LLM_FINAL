import subprocess
import time
import sys 
import requests
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QTextBrowser, QFrame, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.wav import wav_to_laeq_dba


SCENARIO_WAVS = {
    "AC": os.path.join("utils", "wav_files", "AC.wav"),
    "Siren": os.path.join("utils", "wav_files", "Siren.wav"),
    "StreetMusic": os.path.join("utils", "wav_files", "StreetMusic.wav"),
    "Constructionsite": os.path.join("utils", "wav_files", "Constructionsite.wav"),
    "Idlecar engine": os.path.join("utils", "wav_files", "Idlecar engine.wav"),
    "TV Sound": os.path.join("utils", "wav_files", "TV Sound.wav"),
    "ChildrenTalking": os.path.join("utils", "wav_files", "ChildrenTalking.wav"),
    "Horn": os.path.join("utils", "wav_files", "Horn.wav"),
    "DogsBarking": os.path.join("utils", "wav_files", "DogsBarking.wav"),
}
    
class EcoformUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(1280, 1000)
        self.setWindowTitle("Ecoform Acoustic Copilot")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet("background-color: #23272e;")
        self.wav_filename = ""
        self.wav_dba = None
        self.init_ui()

    def init_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(12)

        # TITLE BAR
        title = QLabel("Ecoform Acoustic Copilot")
        title.setStyleSheet("color: #fff; font-size: 28px; font-weight: 800; background:#181a22; padding:18px 18px; border-radius: 16px;")
        root_layout.addWidget(title)

        # Tabs Row
        tabs_layout = QHBoxLayout()
        self.scenario_btn = QPushButton("Scenario Inputs")
        self.geo_btn = QPushButton("Geometry Inputs")
        for btn in [self.scenario_btn, self.geo_btn]:
            btn.setFixedHeight(40)
            btn.setCheckable(True)
        self.scenario_btn.setStyleSheet("background:#ff8300; color:#fff; font-size:14px; border:none; border-radius:10px; padding:4px 28px;")
        self.geo_btn.setStyleSheet("background:#23272e; color:#ccc; font-size:14px; border:none; border-radius:10px; padding:4px 28px;")
        self.scenario_btn.setChecked(True)
        self.geo_btn.setChecked(False)
        tabs_layout.addWidget(self.scenario_btn)
        tabs_layout.addWidget(self.geo_btn)
        tabs_layout.addStretch(1)
        root_layout.addLayout(tabs_layout)

        # MAIN CONTENT AREA: HORIZONTAL SPLIT
        content_layout = QHBoxLayout()
        content_layout.setSpacing(28)
        root_layout.addLayout(content_layout, 8)

        # LEFT: Input Panel with stack (contains scenario_panel and geometry_panel)
        self.inputs_frame = QFrame()
        self.inputs_frame.setStyleSheet("background: #ff8800; border-radius: 20px; padding: 10px;")
        self.inputs_stack = QVBoxLayout(self.inputs_frame)
        self.inputs_stack.setSpacing(0)
        content_layout.addWidget(self.inputs_frame, 1)

        # --- SCENARIO PANEL ---
        self.scenario_panel = QWidget()
        scenario_layout = QVBoxLayout(self.scenario_panel)
        scenario_layout.setSpacing(18)
        self.scenario_select = self._make_orange_box("Select Sound Scenario", list(SCENARIO_WAVS.keys()), scenario_layout)
        self.scenario_select.currentIndexChanged.connect(self.on_scenario_selected)
        self.zone_cb = self._make_orange_box("Zone", ["HD-Urban-V1", "LD-Urban-V1", "Suburban", "GreenEdge-V3"], scenario_layout)
        self.activity_cb = self._make_orange_box("Activity", ["Sleeping", "Working", "Living", "Dining"], scenario_layout)
        self.time_period_cb = self._make_orange_box("Time Period", ["Day", "Night"], scenario_layout)
        wav_box = QFrame()
        wav_box.setStyleSheet("background: #23262e; border-radius: 14px; padding: 20px;")
        wav_layout = QVBoxLayout(wav_box)
        wav_label = QLabel("Upload WAV File for LAeq (manual)")
        wav_label.setStyleSheet("color: #F0E5E5; font-weight: 400; font-size:14px;")
        self.wav_upload_btn = QPushButton("Select WAV File")
        self.wav_upload_btn.setStyleSheet("background: #393e46; color: #F0E5E5; border-radius: 8px; font-size:14px; min-width: 160px;")
        self.wav_upload_btn.clicked.connect(self.upload_wav)
        self.wav_filename_label = QLabel("")
        self.wav_filename_label.setStyleSheet("color: #fff; font-size:13px;")
        wav_layout.addWidget(wav_label)
        wav_layout.addWidget(self.wav_upload_btn)
        wav_layout.addWidget(self.wav_filename_label)
        scenario_layout.addWidget(wav_box)
        self.evaluate_btn = QPushButton("Evaluate Scenario")
        self.evaluate_btn.setStyleSheet("background: #ff8300; color: #fff; font-size:21px; font-weight:800; border-radius: 10px; min-height: 44px;")
        self.evaluate_btn.clicked.connect(self.evaluate_scenario)
        scenario_layout.addWidget(self.evaluate_btn)
        scenario_layout.addStretch(1)

        # --- GEOMETRY PANEL ---
        self.geometry_panel = QWidget()
        geometry_layout = QVBoxLayout(self.geometry_panel)
        geometry_layout.setSpacing(18)
        self.apt_cb = self._make_orange_box("Apartment Type", ["1Bed", "2Bed", "3Bed"], geometry_layout)
        self.floor_le = self._make_orange_lineedit("Floor Level", "e.g. 2", geometry_layout)
        self.wall_cb = self._make_orange_box("Wall Material", ["Painted Brick", "Unpainted Brick", "Concrete Block", "Gypsum Board", "Wood Panel"], geometry_layout)
        self.window_cb = self._make_orange_box("Window Material", ["Double Pane Glass", "Single Pane Glass", "Laminated Glass", "Frosted Glass"], geometry_layout)
        geometry_layout.addStretch(1)

        # Add both panels to the stack but show only one at a time
        self.inputs_stack.addWidget(self.scenario_panel)
        self.inputs_stack.addWidget(self.geometry_panel)
        self.geometry_panel.hide()

        # RIGHT: Vertical split (chat, image)
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(20)

        # CHAT PANEL
        chat_panel = QFrame()
        chat_panel.setStyleSheet("""
            background: #23272e;
            border-radius: 10px;
            padding: 20px;
            border: 2px solid #bfbfbf;   /* Gold-ish, or try #bfbfbf for a light gray */
        """)
        chat_panel.setMinimumWidth(800)
        chat_layout = QVBoxLayout(chat_panel)
        chat_title = QLabel("Ai Acoustic Copilot")
        chat_title.setStyleSheet(" background: #121516; color: #F0E5E5; font-size: 20px; font-weight: 500; margin-bottom: 10px;")
        chat_layout.addWidget(chat_title)
        self.chat_browser = QTextBrowser()
        self.chat_browser.setStyleSheet("""
            background: #121516;
            color: #F0E5E5;
            border-radius: 12px;
            font-size: 20px;
            font-weight: 150;
            padding: 10px;
        """)
        chat_layout.addWidget(self.chat_browser, 9)
        chat_input_row = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Describe your scenario")
        self.chat_input.setMinimumHeight(38)
        self.chat_input.setStyleSheet("background: #31353C; color: #F0E5E5; font-weight: bold; font-size: 17px; border-radius: 8px;")
        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet("background: #31353C; color: #F0E5E5; font-weight: bold; border-radius: 8px; font-size:18px; min-width: 90px;")
        chat_input_row.addWidget(self.chat_input, 6)
        chat_input_row.addWidget(self.send_btn, 1)
        chat_layout.addLayout(chat_input_row)
        right_layout.addWidget(chat_panel, 5)

        # IMAGE PANEL
        image_panel = QFrame()
        image_panel.setStyleSheet("background: #ff8300; border-radius: 16px; padding: 24px;")
        image_layout = QVBoxLayout(image_panel)
        img_label = QLabel("static image from\nactive viewport")
        img_label.setStyleSheet("color: #bbb; font-size: 20px;")
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setFixedSize(440, 260)
        image_layout.addWidget(img_label, stretch=1)
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet("background: #CB7600; color: #fff; font-weight: bold; border-radius: 10px; padding: 10px 20px; font-size:17px;")
        image_layout.addWidget(export_btn, alignment=Qt.AlignRight)
        right_layout.addWidget(image_panel, 4)
        content_layout.addWidget(right_panel, 4)
        btn_row = QHBoxLayout()
        self.heatmap_btn = QPushButton("Heatmap")
        self.heatmap_btn.setStyleSheet("background: #CB7600; color: #fff; font-weight: bold; font-size:17px; border-radius:10px; padding:10px 20px;")
        btn_row.addWidget(self.heatmap_btn)

        self.viewport_btn = QPushButton("Viewport")
        self.viewport_btn.setStyleSheet("background: #CB7600; color: #fff; font-weight: bold; font-size:17px; border-radius:10px; padding:10px 20px;")
        btn_row.addWidget(self.viewport_btn)

        self.capture_btn = QPushButton("Capture")
        self.capture_btn.setStyleSheet("background: #CB7600; color: #fff; font-weight: bold; font-size:17px; border-radius:10px; padding:10px 20px;")
        btn_row.addWidget(self.capture_btn)

        image_layout.addLayout(btn_row)
        self.capture_btn.clicked.connect(lambda: capture_and_update_viewport(self))
        self.heatmap_btn.clicked.connect(lambda: refresh_image_from_rhino(self))    

        # Tab logic
        self.scenario_btn.clicked.connect(self.show_scenario)
        self.geo_btn.clicked.connect(self.show_geometry)
        self.send_btn.clicked.connect(self.on_send_message)
        self.chat_input.returnPressed.connect(self.on_send_message)
        self.show_scenario()

    def _make_orange_box(self, label, options, parent_layout):
        box = QFrame()
        # Darker orange frame, even more contrast for input!
        box.setStyleSheet("background: #ff8800; border-radius: 10px; padding: 11px;")
        vbox = QVBoxLayout(box)
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #fff; font-weight: 800; font-size:16px; margin-bottom:4px;")
        combo = QComboBox()
        combo.addItems(options)
        # Dark contrast for dropdown itself!
        combo.setStyleSheet("""
            QComboBox {
                font-size: 16px;
                background: #2b2d31;  /* much darker */
                color: #fff;
                border-radius: 8px;
                min-width: 170px;
                padding: 4px 6px;
                border: 2px solid #181a22;
            }
            QComboBox QAbstractItemView {
                background: #23262e;
                color: #fff;
                selection-background-color: #ffbb40;
                selection-color: #222;
            }
        """)
        vbox.addWidget(lbl)
        vbox.addWidget(combo)
        parent_layout.addWidget(box)
        return combo


    def _make_orange_lineedit(self, label, placeholder, parent_layout):
        box = QFrame()
        box.setStyleSheet("background: #ff8800; border-radius: 10px; padding: 10px;")
        vbox = QVBoxLayout(box)
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #fff; font-weight: 700; font-size:16px; margin-bottom:4px;")
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setStyleSheet("""
            font-size: 16px;
            background: #2b2d31;
            color: #fff;
            border-radius: 8px;
            min-width: 170px;
            border: 2px solid #181a22;
        """)
        edit.setMinimumHeight(38)
        edit.setMaximumHeight(38)
        vbox.addWidget(lbl)
        vbox.addWidget(edit)
        parent_layout.addWidget(box)
        return edit

    def show_scenario(self):
        self.scenario_panel.show()
        self.geometry_panel.hide()
        self.scenario_btn.setStyleSheet("background:#ff8300; color:#fff; font-size:18px; border:none; border-radius:10px; padding:4px 28px;")
        self.geo_btn.setStyleSheet("background:#23272e; color:#ccc; font-size:18px; border:none; border-radius:10px; padding:4px 28px;")
        self.scenario_btn.setChecked(True)
        self.geo_btn.setChecked(False)

    def show_geometry(self):
        self.scenario_panel.hide()
        self.geometry_panel.show()
        self.scenario_btn.setStyleSheet("background:#23272e; color:#ccc; font-size:18px; border:none; border-radius:10px; padding:4px 28px;")
        self.geo_btn.setStyleSheet("background:#ff8300; color:#fff; font-size:18px; border:none; border-radius:10px; padding:4px 28px;")
        self.scenario_btn.setChecked(False)
        self.geo_btn.setChecked(True)

    def upload_wav(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open WAV file", "", "WAV files (*.wav)")
        if fname:
            self.wav_filename = fname
            self.wav_filename_label.setText(fname.split("/")[-1])
            laeq_dba = wav_to_laeq_dba(fname)
            self.wav_dba = laeq_dba
            self.wav_filename_label.setText(f"{fname.split('/')[-1]} | LAeq: {laeq_dba} dB")

    def on_scenario_selected(self, idx):
        scenario = self.scenario_select.currentText()
        wav_path = SCENARIO_WAVS.get(scenario)
        if wav_path and os.path.exists(wav_path):
            laeq_dba = wav_to_laeq_dba(wav_path)
            self.wav_filename = wav_path
            self.wav_dba = laeq_dba
            self.wav_filename_label.setText(f"{scenario} | LAeq: {laeq_dba} dB")
        else:
            self.wav_filename_label.setText("WAV file not found")
            self.wav_dba = None

    def evaluate_scenario(self):
        print("EVALUATE button clicked")
        zone = self.zone_cb.currentText()
        activity = self.activity_cb.currentText()
        time_period = self.time_period_cb.currentText()
        laeq = self.wav_dba if self.wav_dba is not None else None

        prompt = (f"<b>AI:</b> Evaluate the following acoustic scenario:<br>"
                  f"Zone: {zone}, Activity: {activity}, Time Period: {time_period}, LAeq: {laeq} dB.")
        self.chat_browser.append(f"""
            <div style='background:#ff8300; color:#fff; border-radius:12px; margin:12px 60px 12px 0;
                 padding:12px 20px; font-size:18px; font-weight:600; width:fit-content; display:inline-block;'>
            {prompt}
            </div>
        """)

        try:
            payload = {
                "Zone": zone,
                "activity": activity,
                "Time_Period": time_period,
                "Laeq": laeq if laeq is not None else 0,
            }
            r = requests.post("http://127.0.0.1:8000/predict", json=payload, timeout=10)
            if r.status_code == 200:
                result = r.json().get("result", {})
                result_text = f"<b>Comfort Score:</b> {result.get('comfort_score', '(unknown)')}<br>{result.get('compliance', {}).get('status', '')} {result.get('compliance', {}).get('reason', '')}"
                self.chat_browser.append(f"""
                    <div style='background:#393e46; color:#fff; border-radius:12px; margin:12px 0 12px 60px;
                         padding:12px 20px; font-size:18px; width:fit-content; display:inline-block;'>
                    {result_text}
                    </div>
                """)
            else:
                self.chat_browser.append("<div style='color:red'>Error: No response from backend.</div>")
        except Exception as e:
            self.chat_browser.append(f"<div style='color:red'>Backend error: {e}</div>")

    def on_send_message(self):
        text = self.chat_input.text().strip()
        if not text:
            return
        self.chat_browser.append(f"""
            <div style='background:#393e46; color:#fff; border-radius:12px; margin:12px 0 12px 60px;
                 padding:12px 20px; font-size:18px; text-align:right; width:fit-content; display:inline-block;'>
            You: {text}
            </div>
        """)
        self.chat_input.clear()

if __name__ == "__main__":
    app = QApplication([])
    win = EcoformUI()
    win.show()
    app.exec_()