import sys
import os

os.environ["PYTHONOCC_DISPLAY"] = "pyqt6"
from OCC.Display.backend import load_backend
load_backend("pyqt6")
from OCC.Display.qtDisplay import qtViewer3d

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget,
    QLabel, QComboBox, QPushButton, QTextEdit, QLineEdit, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

import ifcopenshell
import ifcopenshell.geom

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
        self.resize(1440, 820)
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.setStyleSheet(f"background: {COLOR_MAIN_BG};")
        main_layout = QHBoxLayout(self.central)

        # LEFT PANEL (inputs)
        self.left_panel = QWidget()
        self.left_panel.setFixedWidth(400)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setSpacing(16)
        left_layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("Ecoform Acoustic Copilot")
        title.setFont(FONT_TITLE)
        title.setStyleSheet(f"background: {COLOR_TITLE_BG}; color: {COLOR_TITLE_TEXT}; border-radius: 10px; padding: 18px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title)

        # === Tabs: Geometry Inputs and Scenario Inputs ===
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

        # --- Geometry Inputs Tab ---
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

        # --- Scenario Inputs Tab ---
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
        main_layout.addWidget(self.left_panel)

        # RIGHT PANEL (vertical, chatbot on top, viewer always present)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(8)
        right_layout.setContentsMargins(8, 8, 8, 8)

        self.info_panel = QWidget()
        info_layout = QVBoxLayout(self.info_panel)
        self.info_panel.setStyleSheet(
            f"""
            background: {COLOR_CHAT_BG};
            color: {COLOR_CHAT_TEXT};
            border-radius: 14px;
            padding: 18px;
            """
        )
        self.info_title = QLabel("Element Info")
        self.info_title.setFont(FONT_TITLE)
        self.info_title.setStyleSheet(
            f"color: {COLOR_TITLE_TEXT}; font-weight: bold;"
        )
        info_layout.addWidget(self.info_title)
        self.info_text = QLabel("")
        self.info_text.setFont(FONT_BODY)
        self.info_text.setStyleSheet(
            f"color: {COLOR_CHAT_TEXT};"
        )
        info_layout.addWidget(self.info_text)
        self.info_panel.setVisible(False)  # Hide by default
        right_layout.addWidget(self.info_panel)


        # 3D Viewer
        self.viewer = MyViewer(self)
        self.viewer.InitDriver()
        right_layout.addWidget(self.viewer, stretch=1)

        # Action buttons row
        btn_layout = QHBoxLayout()
        for name in ["Heatmap", "Viewport", "Capture", "Export"]:
            btn = QPushButton(name)
            btn.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold;")
            if name == "Heatmap":
                btn.clicked.connect(self.viewer.generate_heatmap)
            btn_layout.addWidget(btn)
        right_layout.addLayout(btn_layout)

        main_layout.addWidget(right_panel)

        # 3D File Upload connection
        threeD_btn.clicked.connect(self.handle_ifc_upload)

        # Chatbot (initially hidden)
        self.chat_panel = QWidget()
        chat_layout = QVBoxLayout(self.chat_panel)
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
        self.chat_panel.setVisible(False)
        right_layout.addWidget(self.chat_panel)

        # --- Show/hide logic ---
        def show_copilot():
            self.left_panel.setVisible(False)
            self.chat_panel.setVisible(True)
        def show_inputs():
            self.left_panel.setVisible(True)
            self.chat_panel.setVisible(False)
        eval_btn.clicked.connect(show_copilot)
        return_btn = QPushButton("Return to Inputs")
        return_btn.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold;")
        chat_layout.addWidget(return_btn)
        return_btn.clicked.connect(show_inputs)

        self.left_panel.setVisible(True)
        self.chat_panel.setVisible(False)

    def handle_ifc_upload(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open IFC", "", "IFC Files (*.ifc)")
        if fname:
            self.viewer.load_ifc_file(fname)

    def on_shape_selected(self, shapes):
        # `shapes` is a list of selected TopoDS_Shapes
        if not shapes:
            return
        shape = shapes[0]
        shape_hash = shape.__hash__()
        ifc_elem = self.shape_to_ifc.get(shape_hash)
        if ifc_elem:
            info = f"IFC Type: {ifc_elem.is_a()}\nGlobalId: {getattr(ifc_elem, 'GlobalId', '')}\nName: {getattr(ifc_elem, 'Name', '')}"
            QMessageBox.information(self, "Element Info", info)
        else:
            QMessageBox.information(self, "Element Info", "No IFC data for this element.")

    def show_ifc_panel(self, ifc_elem):
        from PyQt6.QtWidgets import QMessageBox
        try:
            if ifc_elem:
                info = f"Type: {ifc_elem.is_a()}\nGlobalId: {getattr(ifc_elem, 'GlobalId', '')}"
                QMessageBox.information(self, "IFC Element Information", info)
            else:
                QMessageBox.information(self, "IFC Element Information", "No element selected.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to show IFC panel: {str(e)}")




class MyViewer(qtViewer3d):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_shapes = []
        self.shape_to_ifc = {}  # Map shape IDs to IFC elements
        # Define color mapping for different IFC types
        self.color_map = {
            'IfcWall': (1.0, 0.0, 0.0),      # Red
            'IfcSlab': (0.0, 1.0, 0.0),      # Green
            'IfcBeam': (0.0, 0.0, 1.0),      # Blue
            'IfcColumn': (1.0, 1.0, 0.0),    # Yellow
            'IfcDoor': (1.0, 0.5, 0.0),      # Orange
            'IfcWindow': (0.0, 1.0, 1.0),    # Cyan
            'IfcRoof': (0.5, 0.0, 0.5),      # Purple
            'IfcStair': (0.5, 0.5, 0.0),     # Olive
            'IfcFurniture': (0.0, 0.5, 0.5), # Teal
            'IfcSanitaryTerminal': (0.5, 0.0, 0.0), # Dark Red
        }
        # Default color for unknown types
        self.default_color = (0.7, 0.7, 0.7)  # Gray

    def generate_heatmap_data(self, ifc_elem):
        """Generate heatmap data for an IFC element based on its properties"""
        try:
            # Get element properties
            props = ifc_elem.get_info()
            
            # Calculate a value based on element properties
            # This is a simple example - you can modify this based on your needs
            value = 0.0
            
            # Add value based on element type
            if ifc_elem.is_a() == 'IfcWall':
                value += 0.8
            elif ifc_elem.is_a() == 'IfcSlab':
                value += 0.6
            elif ifc_elem.is_a() == 'IfcBeam':
                value += 0.4
            elif ifc_elem.is_a() == 'IfcColumn':
                value += 0.5
            elif ifc_elem.is_a() == 'IfcDoor':
                value += 0.3
            elif ifc_elem.is_a() == 'IfcWindow':
                value += 0.2
            
            # Add value based on element name if it exists
            if hasattr(ifc_elem, 'Name') and ifc_elem.Name:
                value += 0.1
            
            # Normalize value between 0 and 1
            value = min(max(value, 0.0), 1.0)
            
            return value
        except Exception as e:
            print(f"Error generating heatmap data: {e}")
            return 0.0

    def load_ifc_file(self, path):
        self.shape_to_ifc = {}
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_PYTHON_OPENCASCADE, True)
        ifc = ifcopenshell.open(path)
        products = ifc.by_type("IfcProduct")
        for p in products:
            if hasattr(p, "Representation") and p.Representation:
                try:
                    shape = ifcopenshell.geom.create_shape(settings, p).geometry
                    ais_result = self._display.DisplayShape(shape, update=True)
                    if not isinstance(ais_result, list):
                        ais_result = [ais_result]
                    for ais_obj in ais_result:
                        self.shape_to_ifc[ais_obj] = p
                except Exception as e:
                    print(f"Failed to display {p}: {e}")
        self._display.FitAll()
        # Enable selection mode
        self._display.Context.Activate(0)  # Activate selection mode
        self._display.Context.UpdateSelected(True)

    def generate_heatmap(self):
        """Generate and display heatmap for all IFC elements"""
        try:
            # Create a dictionary to store heatmap values
            heatmap_data = {}
            
            # Generate heatmap data for each IFC element
            for shp, ifc_elem in self.shape_to_ifc.items():
                value = self.generate_heatmap_data(ifc_elem)
                heatmap_data[shp] = value
            
            # Apply heatmap colors
            for shp, value in heatmap_data.items():
                # Convert value to color (red for high values, blue for low)
                color = (value, 0.0, 1.0 - value)  # RGB
                self._display.SetColor_sRGB(shp, color)
            
            self._display.Repaint()
            QMessageBox.information(self, "Heatmap", "Heatmap generated successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate heatmap: {str(e)}")

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        context = self._display.Context
        context.InitSelected()
        ais_shape = None
        while context.MoreSelected():
            ais_shape = context.SelectedInteractive()
            context.NextSelected()
        if ais_shape and ais_shape in self.shape_to_ifc:
            ifc_elem = self.shape_to_ifc[ais_shape]
            main_win = self.parent()
            if hasattr(main_win, 'show_ifc_panel'):
                main_win.show_ifc_panel(ifc_elem)
        else:
            main_win = self.parent()
            if hasattr(main_win, 'show_ifc_panel'):
                main_win.show_ifc_panel(None)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = EcoformMainWindow()
    win.show()
    sys.exit(app.exec())
