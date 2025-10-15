import FreeCAD
import FreeCADGui

# This global variable is needed to hold the panel instance
my_panel = None

class DentaMindAIWorkbench (Workbench):
    """The main DentaMind AI Workbench object."""
    MenuText = "DentaMind AI"
    ToolTip = "AI tools for dental design"

    def Initialize(self):
        """Executed when the workbench is created. All components are defined here."""
        global my_panel
        from PySide import QtGui, QtCore

        # --- NESTED CLASS 1: The Custom UI Panel ---
        class DentaMindPanel:
            def __init__(self):
                self.widget = QtGui.QDockWidget("DentaMind AI Controls")
                self.content = QtGui.QWidget()
                self.widget.setWidget(self.content)
                layout = QtGui.QVBoxLayout(self.content)
                scroll_area = QtGui.QScrollArea()
                scroll_area.setWidgetResizable(True)
                layout.addWidget(scroll_area)
                self.scroll_content = QtGui.QWidget()
                self.scroll_layout = QtGui.QVBoxLayout(self.scroll_content)
                self.scroll_layout.setAlignment(QtCore.Qt.AlignTop)
                scroll_area.setWidget(self.scroll_content)
                main_window = FreeCADGui.getMainWindow()
                main_window.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.widget)
                self.update_scan_list()

            def update_scan_list(self):
                while self.scroll_layout.count():
                    child = self.scroll_layout.takeAt(0)
                    if child.widget(): child.widget().deleteLater()
                
                # CORRECTED: Use FreeCAD.App
                doc = FreeCAD.App.ActiveDocument
                if not doc:
                    self.scroll_layout.addWidget(QtGui.QLabel("No document open."))
                    return
                
                mesh_objects = [o for o in doc.Objects if o.isDerivedFrom("Mesh::Feature")]
                if not mesh_objects:
                    self.scroll_layout.addWidget(QtGui.QLabel("No scans loaded."))
                    return

                for obj in mesh_objects:
                    row = QtGui.QHBoxLayout()
                    row.addWidget(QtGui.QLabel(obj.Label))
                    slider = QtGui.QSlider(QtCore.Qt.Horizontal)
                    slider.setRange(0, 100)
                    slider.setValue(obj.ViewObject.Transparency)
                    slider.valueChanged.connect(lambda val, o=obj.Name: self.set_transparency(o, val))
                    row.addWidget(slider)
                    self.scroll_layout.addLayout(row)
            
            def set_transparency(self, obj_name, value):
                # CORRECTED: Use FreeCAD.App
                doc = FreeCAD.App.ActiveDocument
                if doc:
                    obj = doc.getObject(obj_name)
                    if obj:
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
                    # CORRECTED: Use FreeCAD.App
                    doc = FreeCAD.App.ActiveDocument or FreeCAD.App.newDocument("PatientCase")
                    for path in paths:
                        import Mesh
                        Mesh.insert(path, doc.Name)
                    FreeCADGui.activeDocument().activeView().fitAll()
            def GetResources(self):
                return {'Pixmap': '', 'MenuText': 'Import Scans', 'ToolTip': 'Load patient STL files'}

        # --- Initialization Logic ---
        self.observer = DocumentObserver()
        my_panel = DentaMindPanel()
        
        FreeCADGui.addCommand('DentaMindAI_ImportScans', ImportScansCmd())
        self.toolbar = ["DentaMindAI_ImportScans"]
        self.appendToolbar("DentaMind AI Tools", self.toolbar)
        
    def Activated(self):
        """Executed when the workbench is switched to."""
        # CORRECTED: Use FreeCAD.App
        FreeCAD.App.addObserver(self.observer)
        if my_panel:
            my_panel.widget.show()
            my_panel.update_scan_list()
        print("DentaMind AI Workbench Activated.")

    def Deactivated(self):
        """Executed when the workbench is switched away from."""
        # CORRECTED: Use FreeCAD.App
        FreeCAD.App.removeObserver(self.observer)
        if my_panel:
            my_panel.widget.hide()
        print("DentaMind AI Workbench Deactivated.")

# --- Register the Workbench with FreeCAD ---
FreeCADGui.addWorkbench(DentaMindAIWorkbench())