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
from PyQt6.QtCore import Qt, QTimer
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

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

class MyViewer(qtViewer3d):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shape_to_ifc = {}
        # Color mapping for types (for heatmap etc)
        self.color_map = {
            'IfcWall': (1.0, 0.0, 0.0),
            'IfcSlab': (0.0, 1.0, 0.0),
            'IfcBeam': (0.0, 0.0, 1.0),
            'IfcColumn': (1.0, 1.0, 0.0),
            'IfcDoor': (1.0, 0.5, 0.0),
            'IfcWindow': (0.0, 1.0, 1.0),
            'IfcRoof': (0.5, 0.0, 0.5),
            'IfcStair': (0.5, 0.5, 0.0),
            'IfcFurniture': (0.0, 0.5, 0.5),
            'IfcSanitaryTerminal': (0.5, 0.0, 0.0),
        }
        self.default_color = (0.7, 0.7, 0.7)

    def generate_heatmap_data(self, ifc_elem):
        # Dummy logic, customize as needed
        value = 0.0
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
        if hasattr(ifc_elem, 'Name') and ifc_elem.Name:
            value += 0.1
        return min(max(value, 0.0), 1.0)

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
        self._display.Context.Activate(0)  # Activate selection mode

    def generate_heatmap(self):
        try:
            heatmap_data = {}
            for shp, ifc_elem in self.shape_to_ifc.items():
                value = self.generate_heatmap_data(ifc_elem)
                heatmap_data[shp] = value
            for shp, value in heatmap_data.items():
                color = (value, 0.0, 1.0 - value)
                color_obj = Quantity_Color(color[0], color[1], color[2], Quantity_TOC_RGB)
                self._display.Context.SetColor(shp, color_obj, False)
            self._display.Repaint()
            QMessageBox.information(self, "Heatmap", "Heatmap generated successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate heatmap: {str(e)}")


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

        self.viewer = MyViewer(self)
        self.viewer.InitDriver()
        right_layout.addWidget(self.viewer, stretch=1)
        main_layout.addWidget(right_panel)

        # Action buttons row
        btn_layout = QHBoxLayout()
        for name in ["Heatmap", "Viewport", "Capture", "Export"]:
            btn = QPushButton(name)
            btn.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold;")
            if name == "Heatmap":
                btn.clicked.connect(self.viewer.generate_heatmap)
            btn_layout.addWidget(btn)
        right_layout.addLayout(btn_layout)

        # 3D File Upload connection
        threeD_btn.clicked.connect(self.handle_ifc_upload)

        # Selection polling for OCC
        self.last_selected = None
        self.selection_timer = QTimer(self)
        self.selection_timer.timeout.connect(self.check_occ_selection)
        self.selection_timer.start(200)

    def handle_ifc_upload(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open IFC", "", "IFC Files (*.ifc)")
        if fname:
            self.viewer.load_ifc_file(fname)

    def check_occ_selection(self):
        context = self.viewer._display.Context
        context.InitSelected()
        ais_shape = None
        while context.MoreSelected():
            ais_shape = context.SelectedInteractive()
            context.NextSelected()
        if ais_shape and ais_shape != self.last_selected:
            self.last_selected = ais_shape
            if ais_shape in self.viewer.shape_to_ifc:
                ifc_elem = self.viewer.shape_to_ifc[ais_shape]
                self.show_ifc_panel(ifc_elem)
            else:
                self.show_ifc_panel(None)
        elif not ais_shape:
            self.last_selected = None
# """ 
#     def show_ifc_panel(self, ifc_elem):
#         try:
#             if ifc_elem:
#                 info = f"Type: {ifc_elem.is_a()}\nGlobalId: {getattr(ifc_elem, 'GlobalId', '')}"
#                 QMessageBox.information(self, "IFC Element Information", info)
#             else:
#                 QMessageBox.information(self, "IFC Element Information", "No element selected.")
#         except Exception as e:
#             QMessageBox.warning(self, "Error", f"Failed to show IFC panel: {str(e)}") """

    def show_ifc_panel(self, ifc_elem):
        try:
            if ifc_elem:
                info = (
                    "<span style='color:#FDF6F6; font-family:Segoe UI;'>"
                    f"<b>Type:</b> {ifc_elem.is_a()}<br>"
                    f"<b>GlobalId:</b> {getattr(ifc_elem, 'GlobalId', '')}<br>"
                    "</span>"
                )
                QMessageBox.information(self, "IFC Element Information", info)
            else:
                QMessageBox.information(self, "IFC Element Information", "<span style='color:#FDF6F6;'>No element selected.</span>")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to show IFC panel: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = EcoformMainWindow()
    win.show()
    sys.exit(app.exec())
