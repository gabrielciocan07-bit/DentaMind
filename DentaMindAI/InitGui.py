import FreeCAD
import FreeCADGui

# This global variable is needed to hold our panel so commands can access it
my_panel = None

class DentaMindAIWorkbench (Workbench):
    """The main DentaMind AI Workbench object."""
    MenuText = "DentaMind AI"
    ToolTip = "AI tools for dental design"

    def Initialize(self):
        """Executed once when the workbench is created."""
        global my_panel
        from PySide import QtGui, QtCore

        # --- NESTED CLASS 1: The Permanent UI Panel ---
        class DentaMindPanel:
            def __init__(self):
                # --- Main Panel Setup ---
                self.widget = QtGui.QDockWidget("DentaMind AI Controls")
                self.content = QtGui.QWidget()
                self.widget.setWidget(self.content)
                self.layout = QtGui.QVBoxLayout(self.content)
                self.layout.setAlignment(QtCore.Qt.AlignTop)

                # --- Scan List Section ---
                self.layout.addWidget(QtGui.QLabel("<b>Loaded Scans</b>"))
                self.scroll_area = QtGui.QScrollArea()
                self.scroll_area.setWidgetResizable(True)
                self.layout.addWidget(self.scroll_area)
                self.scroll_content = QtGui.QWidget()
                self.scroll_layout = QtGui.QVBoxLayout(self.scroll_content)
                self.scroll_layout.setAlignment(QtCore.Qt.AlignTop)
                self.scroll_area.setWidget(self.scroll_content)

                # --- Separator ---
                separator = QtGui.QFrame()
                separator.setFrameShape(QtGui.QFrame.HLine)
                separator.setFrameShadow(QtGui.QFrame.Sunken)
                self.layout.addWidget(separator)

                # --- NEW: Editing Tools Section ---
                self.layout.addWidget(QtGui.QLabel("<b>Editing Tools</b>"))
                self.paint_mode_checkbox = QtGui.QCheckBox("Activate Paint Brush")
                self.layout.addWidget(self.paint_mode_checkbox)

                # Brush radius slider
                radius_layout = QtGui.QHBoxLayout()
                radius_layout.addWidget(QtGui.QLabel("Brush Radius:"))
                self.radius_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
                self.radius_slider.setRange(1, 20) # Radius from 1mm to 20mm
                self.radius_slider.setValue(5)
                radius_layout.addWidget(self.radius_slider)
                self.layout.addLayout(radius_layout)
                
                # Add the panel to the main FreeCAD window
                main_window = FreeCADGui.getMainWindow()
                main_window.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.widget)
                self.update_scan_list()

            def update_scan_list(self):
                # (This function remains the same as before)
                while self.scroll_layout.count():
                    child = self.scroll_layout.takeAt(0)
                    if child.widget(): child.widget().deleteLater()
                doc = FreeCAD.ActiveDocument
                if not doc or not [o for o in doc.Objects if o.isDerivedFrom("Mesh::Feature")]:
                    self.scroll_layout.addWidget(QtGui.QLabel("No scans loaded."))
                    return
                for obj in [o for o in doc.Objects if o.isDerivedFrom("Mesh::Feature")]:
                    row = QtGui.QHBoxLayout()
                    row.addWidget(QtGui.QLabel(obj.Label))
                    slider = QtGui.QSlider(QtCore.Qt.Horizontal)
                    slider.setRange(0, 100)
                    slider.setValue(obj.ViewObject.Transparency)
                    slider.valueChanged.connect(lambda val, o=obj.Name: self.set_transparency(o, val))
                    row.addWidget(slider)
                    self.scroll_layout.addLayout(row)
            
            def set_transparency(self, obj_name, value):
                doc = FreeCAD.ActiveDocument
                if doc and (obj := doc.getObject(obj_name)):
                    obj.ViewObject.Transparency = value
        
        # --- NESTED CLASS 2: The Document Observer ---
        class DocumentObserver:
            def addObject(self, doc, obj):
                if my_panel:
                    my_panel.update_scan_list()

        # --- NESTED CLASS 3: The Import Command ---
        class ImportScansCmd:
            def Activated(self):
                paths, _ = QtGui.QFileDialog.getOpenFileNames(None, "Select STL scans", "", "STL Files (*.stl)")
                if paths:
                    doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("PatientCase")
                    for path in paths:
                        import Mesh
                        Mesh.insert(path, doc.Name)
                    FreeCADGui.activeDocument().activeView().fitAll()

            def GetResources(self):
                return {'Pixmap': '', 'MenuText': 'Import Scans', 'ToolTip': 'Load patient STL files'}

        # --- Initialization Logic (runs only once) ---
        self.observer = DocumentObserver()
        my_panel = DentaMindPanel()
        FreeCADGui.addCommand('DentaMindAI_ImportScans', ImportScansCmd())
        self.toolbar = ["DentaMindAI_ImportScans"]
        self.appendToolbar("DentaMind AI Tools", self.toolbar)
        
    def Activated(self):
        """Executed when you switch TO this workbench."""
        FreeCAD.addObserver(self.observer)
        if my_panel:
            my_panel.widget.show()
            my_panel.update_scan_list()
        print("DentaMind AI Workbench Activated.")

    def Deactivated(self):
        """Executed when you switch AWAY from this workbench."""
        FreeCAD.removeObserver(self.observer)
        if my_panel:
            my_panel.widget.hide()
        print("DentaMind AI Workbench Deactivated.")

# --- Register the Workbench with FreeCAD ---
FreeCADGui.addWorkbench(DentaMindAIWorkbench())