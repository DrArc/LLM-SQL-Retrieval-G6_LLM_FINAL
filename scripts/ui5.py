import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sqlite3

from scripts.recommend_recompute import run_acoustic_prediction
from scripts.sql_query_handler import handle_llm_query as handle_llm_sql
from scripts.llm_acoustic_query_handler import handle_llm_query as handle_llm_acoustic
from scripts.acoustic_pipeline import run_pipeline, run_from_free_text


os.environ["PYTHONOCC_DISPLAY"] = "pyqt6"
from OCC.Display.backend import load_backend
load_backend("pyqt6")
from OCC.Display.qtDisplay import qtViewer3d
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget,
    QLabel, QComboBox, QPushButton, QTextEdit, QLineEdit, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer

import ifcopenshell
import ifcopenshell.geom

# ---- Color and Font scheme ----
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
BG_MAIN = "#181A1B"
BG_PANEL = "#23262B"
ACCENT = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF9500, stop:1 #FF7F50)"
INPUT_BG = "#2E3238"
BORDER_ACCENT = "#FF9500"
TEXT_MAIN = "#F4F4F7"
TEXT_ACCENT = "#FFA040"

# ---- Style definitions ----
panel_style = f"background: {BG_PANEL}; border: 2px solid {BORDER_ACCENT}; border-radius: 8px;"
btn_style = f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold; border-radius: 6px; padding: 8px;"
input_style = f"background: {INPUT_BG}; color: {TEXT_MAIN}; border: 2px solid {BORDER_ACCENT}; border-radius: 4px; padding: 6px;"
chat_style = f"background: {COLOR_CHAT_BG}; color: {COLOR_CHAT_TEXT}; border: 2px solid {BORDER_ACCENT}; border-radius: 6px;"
tab_style = f"QTabWidget::pane {{ border: 2px solid {BORDER_ACCENT}; background: {BG_PANEL}; }} QTabBar::tab {{ background: {COLOR_TAB_BG}; color: {COLOR_TAB_TEXT}; padding: 8px; }} QTabBar::tab:selected {{ background: {COLOR_INPUT_BG}; }}"

FONT_TITLE = QFont("Segoe UI", 20, QFont.Weight.Bold)
FONT_LABEL = QFont("Segoe UI", 12, QFont.Weight.DemiBold)
FONT_BODY = QFont("Segoe UI", 11)
FONT_BUTTON = QFont("Segoe UI", 12, QFont.Weight.Bold)


class MyViewer(qtViewer3d):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shape_to_ifc = {}
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


    
    def extract_model_data(self):
        """
        Extract key acoustic/ML features from the active IFC model.
        Returns a list of dicts (one per element/space), ready for ML or DB use.
        """
        result = []
        for ifc_elem in self.viewer.shape_to_ifc.values():
            entry = {
                "space": getattr(ifc_elem, "LongName", "") or getattr(ifc_elem, "Name", ""), # Space/room name
                "material": "",      # We'll try to extract the main material (see below)
                "element_type": ifc_elem.is_a(),
                "RT60": None,
                "SPL": None,
            }
            # --- Attempt to extract main material name ---
            # This tries a typical IFC "materials" path. Adapt as needed for your models!
            try:
                if hasattr(ifc_elem, "HasAssociations"):
                    for assoc in ifc_elem.HasAssociations:
                        if assoc.is_a("IfcRelAssociatesMaterial"):
                            mats = assoc.RelatingMaterial
                            if hasattr(mats, "Name"):
                                entry["material"] = mats.Name
                            elif hasattr(mats, "ForLayerSet"):  # For layered elements
                                entry["material"] = ", ".join(
                                    [lay.Material.Name for lay in mats.ForLayerSet.MaterialLayers if hasattr(lay.Material, "Name")]
                                )
            except Exception as e:
                pass

            # --- RT60/SPL: if they're properties, extract from property sets ---
            if hasattr(ifc_elem, "IsDefinedBy"):
                for definition in ifc_elem.IsDefinedBy:
                    if definition.is_a("IfcRelDefinesByProperties"):
                        prop_set = definition.RelatingPropertyDefinition
                        if prop_set.is_a("IfcPropertySet"):
                            for prop in prop_set.HasProperties:
                                if prop.is_a("IfcPropertySingleValue"):
                                    pname = prop.Name.lower()
                                    if "rt60" in pname:
                                        entry["RT60"] = float(getattr(getattr(prop, "NominalValue", None), "wrappedValue", 0))
                                    if "spl" in pname:
                                        entry["SPL"] = float(getattr(getattr(prop, "NominalValue", None), "wrappedValue", 0))
            result.append(entry)
        return result

    def save_model_data_to_db(self, db_path="sql/ifc_model_data.db"):
        data = self.extract_model_data()
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS elements (
                model_id TEXT,      -- (optional, you can set to filename or hash)
                space TEXT,
                material TEXT,
                element_type TEXT,
                RT60 REAL,
                SPL REAL
            )
        """)
        # You can clear and re-add for this model if you want uniqueness
        # model_id = self.last_loaded_model_path (store this when loading)
        model_id = getattr(self, "last_loaded_model_path", "unknown")
        c.execute("DELETE FROM elements WHERE model_id=?", (model_id,))
        for entry in data:
            c.execute(
                "INSERT INTO elements (model_id, space, material, element_type, RT60, SPL) VALUES (?, ?, ?, ?, ?, ?)",
                (model_id, entry["space"], entry["material"], entry["element_type"], entry["RT60"], entry["SPL"])
            )
        conn.commit()
        conn.close()
   
    
    def generate_heatmap_data(self, ifc_elem):
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
        self._display.Context.Activate(0)

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

        # -- LEFT PANEL --
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

        # --- Tabs for Inputs ---
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
        self.geo_apartment = QComboBox()
        self.geo_apartment.addItems(["1Bed", "2Bed", "3Bed"])
        self.geo_apartment.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        geo_layout.addWidget(self.geo_apartment)

        geo_layout.addWidget(QLabel("Wall Material:", font=FONT_LABEL))
        self.geo_wall = QComboBox()
        self.geo_wall.addItems([
            "Painted Brick", "Unpainted Brick", "Concrete Block (Coarse)", "Concrete Block (Painted)",
            "Gypsum Board", "Plaster on Masonry", "Plaster with Wallpaper Backing", "Wood Paneling",
            "Acoustic Plaster", "Fiberglass Board"])
        self.geo_wall.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        geo_layout.addWidget(self.geo_wall)

        geo_layout.addWidget(QLabel("Window Material:", font=FONT_LABEL))
        self.geo_window = QComboBox()
        self.geo_window.addItems([
            "Single Pane Glass", "Double Pane Glass", "Laminated Glass", "Wired Glass", "Frosted Glass",
            "Insulated Glazing Unit", "Glass Block", "Glazed Ceramic Tile", "Large Pane Glass", "Small Pane Glass"])
        self.geo_window.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        geo_layout.addWidget(self.geo_window)

        geo_layout.addWidget(QLabel("Floor Material:", font=FONT_LABEL))
        self.geo_floor = QComboBox()
        self.geo_floor.addItems([
            "Marble", "Terrazzo", "Vinyl Tile", "Wood Parquet", "Wood Flooring on Joists",
            "Thin Carpet on Concrete", "Thin Carpet on Wood", "Medium Pile Carpet", "Thick Pile Carpet", "Cork Floor Tiles"])
        self.geo_floor.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        geo_layout.addWidget(self.geo_floor)
        tabs.addTab(geo_tab, "Geometry Inputs")

        # --- Scenario Inputs Tab ---
        scenario_tab = QWidget()
        scenario_layout = QVBoxLayout(scenario_tab)
        scenario_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scenario_layout.addWidget(QLabel("Zone Sound Scenario:", font=FONT_LABEL))
        self.scenario_box = QComboBox()
        self.scenario_box.addItems([
            "High density + High traffic", "High density + Medium traffic", "High density + Light traffic",
            "Medium density + High traffic", "Medium density + Medium traffic", "Medium density + Light traffic",
            "Low density + High traffic", "Low density + Medium traffic", "Low density + Light traffic"])
        self.scenario_box.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        scenario_layout.addWidget(self.scenario_box)

        scenario_layout.addWidget(QLabel("Zone:", font=FONT_LABEL))
        self.zone_box = QComboBox()
        self.zone_box.addItems([
            "HD-Urban-V1", "MD-Urban-V2", "LD-Urban-V3", "Ind-Zone-V0",
            "Roadside-V1", "Roadside-V2", "Roadside-V3", "GreenEdge-V3"])
        self.zone_box.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        scenario_layout.addWidget(self.zone_box)

        scenario_layout.addWidget(QLabel("Activity:", font=FONT_LABEL))
        self.activity_box = QComboBox()
        self.activity_box.addItems([
            "Sleeping", "Working", "Living", "Dining", "Learning", "Healing", "Exercise", "Co-working"])
        self.activity_box.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        scenario_layout.addWidget(self.activity_box)

        scenario_layout.addWidget(QLabel("Time Period:", font=FONT_LABEL))
        self.time_box = QComboBox()
        self.time_box.addItems(["Day", "Night"])
        self.time_box.setStyleSheet(f"background: {COLOR_DROPDOWN_BG}; color: {COLOR_INPUT_TEXT}; border: 2px solid {COLOR_DROPDOWN_FRAME};")
        scenario_layout.addWidget(self.time_box)

        scenario_layout.addWidget(QLabel("Custom Sound Upload (WAV):", font=FONT_LABEL))
        self.upload_btn = QPushButton("Upload WAV File")
        self.upload_btn.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold;")
        scenario_layout.addWidget(self.upload_btn)

        tabs.addTab(scenario_tab, "Scenario Inputs")
        left_layout.addWidget(tabs)

        self.threeD_btn = QPushButton("3D File Upload")
        self.threeD_btn.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold;")
        left_layout.addWidget(self.threeD_btn)

        self.eval_btn = QPushButton("Evaluate Scenario")
        self.eval_btn.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold; font-size: 16px; border-radius: 8px;")
        left_layout.addWidget(self.eval_btn)
        left_layout.addStretch(1)
        main_layout.addWidget(self.left_panel)

        # -- RIGHT PANEL: all widgets created only once! --
        # Chatbot panel
        self.chat_panel = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_panel)
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet(f"background: {COLOR_CHAT_BG}; color: {COLOR_CHAT_TEXT}; font-weight: bold;")
        self.chat_layout.addWidget(self.chat_history)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your question...")
        self.chat_layout.addWidget(self.chat_input)
        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold;")
        self.send_btn.clicked.connect(self.on_chatbot_send)
        self.chat_layout.addWidget(self.send_btn)

        # 3D Viewer
        self.viewer = MyViewer(self)
        self.viewer.InitDriver()

        # Right panel layout
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(8)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.addWidget(self.chat_panel)
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

        # Return to Inputs button
        self.return_to_inputs_btn = QPushButton("Return to Inputs")
        self.return_to_inputs_btn.setStyleSheet(f"background: {COLOR_INPUT_BG}; color: {COLOR_INPUT_TEXT}; font-weight: bold;")
        self.return_to_inputs_btn.clicked.connect(self.show_inputs_panel)
        right_layout.addWidget(self.return_to_inputs_btn)

        main_layout.addWidget(right_panel)

        # --- BUTTON CONNECTIONS ---
        self.threeD_btn.clicked.connect(self.handle_ifc_upload)
        self.eval_btn.clicked.connect(self.on_evaluate_clicked)

        # --- OCC Selection Polling ---
        self.last_selected = None
        self.selection_timer = QTimer(self)
        self.selection_timer.timeout.connect(self.check_occ_selection)
        self.selection_timer.start(200)

        self.left_panel.setStyleSheet(panel_style)
        self.eval_btn.setStyleSheet(btn_style)
        self.threeD_btn.setStyleSheet(btn_style)
        self.geo_apartment.setStyleSheet(input_style)
        self.geo_wall.setStyleSheet(input_style)
        self.geo_window.setStyleSheet(input_style)
        self.geo_floor.setStyleSheet(input_style)
        self.chat_history.setStyleSheet(chat_style)
        tabs.setStyleSheet(tab_style)

    
    def show_inputs_panel(self):
        self.left_panel.setVisible(True)

    def get_geometry_summary(self):
        # For example, count elements by type:
        from collections import Counter
        summary = Counter([ifc_elem.is_a() for ifc_elem in self.viewer.shape_to_ifc.values()])
        # Or get a list of all wall names:
        wall_names = [e.Name for e in self.viewer.shape_to_ifc.values() if e.is_a() == "IfcWall"]
        # Return as a string, JSON, or dict, whatever the LLM can use
        return {
            "element_counts": dict(summary),
            "wall_names": wall_names
    }

    def on_chatbot_send(self):
        question = self.chat_input.text().strip()
        if not question:
            return

        self.chat_history.append(f"<b>You:</b> {question}")
        self.chat_input.clear()

        try:
            # Try LLM-driven pipeline
            response = run_from_free_text(question)
            if "error" in response:
                self.chat_history.append(f"<span style='color:red;'>⚠️ {response['error']}</span>")
            else:
                self.chat_history.append(f"<span style='color:#E98801;'><b>AI:</b> {response['summary']}</span>")
        except Exception as e:
            self.chat_history.append(f"<span style='color:red;'>[Error]: {e}</span>")

    def handle_ifc_upload(self):
        start_path = getattr(self, "last_loaded_model_path", os.path.expanduser("~"))
        fname, _ = QFileDialog.getOpenFileName(self, "Open IFC", start_path, "IFC Files (*.ifc)")
        if fname:
            self.viewer.load_ifc_file(fname)
            self.save_model_data_to_db()  # Optionally save features for ML

    def on_evaluate_clicked(self):
        self.left_panel.setVisible(False)  # Hide inputs, show only viewer and chat

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
