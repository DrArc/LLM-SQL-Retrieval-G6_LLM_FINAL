import sys
import os
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget,
    QLabel, QComboBox, QPushButton, QStackedWidget, QTextEdit, QLineEdit
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QUrl

# COLOR AND FONT SCHEME
COLOR_TITLE_BG = "#2C2C2C"
COLOR_TITLE_TEXT = "#FDF6F6"
COLOR_TAB_BG = "#FF8A05"
COLOR_TAB_TEXT = "#FDF6F6"
COLOR_DROPDOWN_FRAME = "#E98801"
COLOR_DROPDOWN_BG = "#31353C"
COLOR_INPUT_BG = "#FF8F04"
COLOR_INPUT_TEXT = "#FDF6F6"
COLOR_CHAT_BG = "#2C2C2C"
COLOR_CHAT_TEXT = "#FDF6F6"
COLOR_MAIN_BG = "#121516"

FONT_TITLE = QFont("Segoe UI", 16, QFont.Weight.Bold)
FONT_LABEL = QFont("Segoe UI", 12, QFont.Weight.Bold)
FONT_BODY = QFont("Segoe UI", 11)
FONT_BUTTON = QFont("Segoe UI", 12, QFont.Weight.Bold)

class EcoformMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ecoform Acoustic Copilot")
        self.resize(1300, 800)
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.setStyleSheet(f"background: {COLOR_MAIN_BG};")
        main_layout = QHBoxLayout(self.central)

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        html_path = os.path.join(project_root, "web", "dist", "index.html")
        self.viewer = QWebEngineView()
        print("Loading URL:", "http://localhost:8000/index.html")
        self.viewer.load(QUrl("http://localhost:8000/index.html"))






        # --- LEFT PANEL (unchanged) ---
        left_panel = QWidget()
        left_panel.setFixedWidth(380)
        left_panel.setStyleSheet(f"background: {COLOR_TAB_BG}; border-radius: 12px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(16)
        left_layout.setContentsMargins(8, 8, 8, 8)
        title = QLabel("Ecoform Acoustic Copilot")
        title.setFont(FONT_TITLE)
        title.setStyleSheet(f"background: {COLOR_TITLE_BG}; color: {COLOR_TITLE_TEXT}; border-radius: 10px; padding: 18px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; }}
            QTabBar::tab {{
                background: {COLOR_TAB_BG};
                color: {COLOR_TAB_TEXT};
                font-weight: bold; padding: 8px 20px; border-radius: 10px;
            }}
            QTabBar::tab:selected {{ background: {COLOR_DROPDOWN_FRAME}; }}
        """)
        # Geometry Inputs Tab (unchanged)
        geo_tab = QWidget()
        geo_layout = QVBoxLayout(geo_tab)
        geo_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        geo_layout.addWidget(QLabel("Apartment Type Group:", font=FONT_LABEL))
        geo_apartment = QComboBox()
        geo_apartment.addItems(["1Bed", "2Bed", "3Bed"])
        geo_apartment.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        geo_layout.addWidget(geo_apartment)
        geo_layout.addWidget(QLabel("Wall Material:", font=FONT_LABEL))
        geo_wall = QComboBox()
        geo_wall.addItems([
            "Painted Brick", "Unpainted Brick", "Concrete Block (Coarse)", "Concrete Block (Painted)",
            "Gypsum Board", "Plaster on Masonry", "Plaster with Wallpaper Backing", "Wood Paneling",
            "Acoustic Plaster", "Fiberglass Board"])
        geo_wall.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        geo_layout.addWidget(geo_wall)
        geo_layout.addWidget(QLabel("Window Material:", font=FONT_LABEL))
        geo_window = QComboBox()
        geo_window.addItems([
            "Single Pane Glass", "Double Pane Glass", "Laminated Glass", "Wired Glass", "Frosted Glass",
            "Insulated Glazing Unit", "Glass Block", "Glazed Ceramic Tile", "Large Pane Glass", "Small Pane Glass"])
        geo_window.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        geo_layout.addWidget(geo_window)
        geo_layout.addWidget(QLabel("Floor Material:", font=FONT_LABEL))
        geo_floor = QComboBox()
        geo_floor.addItems([
            "Marble", "Terrazzo", "Vinyl Tile", "Wood Parquet", "Wood Flooring on Joists",
            "Thin Carpet on Concrete", "Thin Carpet on Wood", "Medium Pile Carpet", "Thick Pile Carpet", "Cork Floor Tiles"])
        geo_floor.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        geo_layout.addWidget(geo_floor)
        tabs.addTab(geo_tab, "Geometry Inputs")

        # Scenario Inputs Tab (unchanged)
        scenario_tab = QWidget()
        scenario_layout = QVBoxLayout(scenario_tab)
        scenario_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scenario_layout.addWidget(QLabel("Zone Sound Scenario:", font=FONT_LABEL))
        scenario_box = QComboBox()
        scenario_box.addItems([
            "High density + High traffic", "High density + Medium traffic", "High density + Light traffic",
            "Medium density + High traffic", "Medium density + Medium traffic", "Medium density + Light traffic",
            "Low density + High traffic", "Low density + Medium traffic", "Low density + Light traffic"])
        scenario_box.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        scenario_layout.addWidget(scenario_box)
        scenario_layout.addWidget(QLabel("Zone:", font=FONT_LABEL))
        zone_box = QComboBox()
        zone_box.addItems([
            "HD-Urban-V1", "MD-Urban-V2", "LD-Urban-V3", "Ind-Zone-V0",
            "Roadside-V1", "Roadside-V2", "Roadside-V3", "GreenEdge-V3"])
        zone_box.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        scenario_layout.addWidget(zone_box)
        scenario_layout.addWidget(QLabel("Activity:", font=FONT_LABEL))
        activity_box = QComboBox()
        activity_box.addItems([
            "Sleeping", "Working", "Living", "Dining", "Learning", "Healing", "Exercise", "Co-working"])
        activity_box.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        scenario_layout.addWidget(activity_box)
        scenario_layout.addWidget(QLabel("Time Period:", font=FONT_LABEL))
        time_box = QComboBox()
        time_box.addItems(["Day", "Night"])
        time_box.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        scenario_layout.addWidget(time_box)
        scenario_layout.addWidget(QLabel("Custom Sound Upload (WAV):", font=FONT_LABEL))
        upload_btn = QPushButton("Upload WAV File")
        upload_btn.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold;")
        scenario_layout.addWidget(upload_btn)
        tabs.addTab(scenario_tab, "Scenario Inputs")
        left_layout.addWidget(tabs)
        threeD_btn = QPushButton("3D File Upload")
        threeD_btn.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold;")
        left_layout.addWidget(threeD_btn)
        eval_btn = QPushButton("Evaluate Scenario")
        eval_btn.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold; font-size: 16px; border-radius: 8px;")
        left_layout.addWidget(eval_btn)
        left_layout.addStretch(1)
        main_layout.addWidget(left_panel)

        # --- RIGHT STACK ---
        self.right_stack = QStackedWidget()

        # --- Chatbot panel (unchanged) ---
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_title = QLabel("AI Acoustic Copilot")
        chat_title.setFont(FONT_TITLE)
        chat_title.setStyleSheet(f"background: {COLOR_CHAT_BG}; color: {COLOR_CHAT_TEXT}; border-radius: 10px; padding: 10px;")
        chat_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chat_layout.addWidget(chat_title)
        chat_history = QTextEdit()
        chat_history.setReadOnly(True)
        chat_history.setStyleSheet(f"background: {COLOR_CHAT_BG}; color: {COLOR_CHAT_TEXT}; font-weight: bold;")
        chat_layout.addWidget(chat_history)
        chat_input = QLineEdit()
        chat_input.setPlaceholderText("Describe your scenario")
        chat_input.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold;")
        chat_layout.addWidget(chat_input)
        send_btn = QPushButton("Send")
        send_btn.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold;")
        chat_layout.addWidget(send_btn)
        self.right_stack.addWidget(chat_widget)

        # --- Viewer panel (clean, only once) ---
        viewer_widget = QWidget()
        viewer_layout = QVBoxLayout(viewer_widget)
        self.viewer = QWebEngineView()
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        html_path = os.path.join(project_root, "web", "dist", "index.html")
        self.viewer.load(QUrl.fromLocalFile(html_path))
        viewer_layout.addWidget(self.viewer)
        # Add model URL input and Load button
        self.model_url_input = QLineEdit()
        self.model_url_input.setPlaceholderText("Paste Speckle Model URL here")
        viewer_layout.addWidget(self.model_url_input)
        load_btn = QPushButton("Load Model")
        load_btn.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold;")
        load_btn.clicked.connect(self.load_model)
        viewer_layout.addWidget(load_btn)
        # Action buttons
        btn_layout = QHBoxLayout()
        for name in ["Heatmap", "Viewport", "Capture", "Export"]:
            btn = QPushButton(name)
            btn.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold;")
            btn_layout.addWidget(btn)
        viewer_layout.addLayout(btn_layout)
        self.right_stack.addWidget(viewer_widget)
        main_layout.addWidget(self.right_stack)

        # --- Button wiring ---
        eval_btn.clicked.connect(lambda: self.right_stack.setCurrentIndex(0))
        self.right_stack.setCurrentIndex(1)
        self.viewer.loadFinished.connect(self.load_default_model)

    def load_model(self):
        url = self.model_url_input.text()
        if url:
            self.viewer.page().runJavaScript(f'window.startSpeckleViewer("{url}")')

    def load_default_model(self):
        # Called after initial HTML load
        url = "https://macad.speckle.xyz/projects/ed979a4aae/models/09a0059178"
        self.viewer.page().runJavaScript(f'startSpeckleViewer("{url}")')
        token = ""
        self.viewer.page().runJavaScript(f'startSpeckleViewer("{url}", "{token}")')
        self.viewer.loadFinished.connect(self.load_default_model)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = EcoformMainWindow()
    win.show()
    sys.exit(app.exec())