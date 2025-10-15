import FreeCAD
import FreeCADGui

# --- 1. DEFINE ALL CLASSES FIRST ---

class DentaMindTaskPanel:
    """The main user interface panel that appears on the left."""
    def __init__(self):
        from PySide import QtGui, QtCore
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("DentaMind AI Controls")
        self.layout = QtGui.QVBoxLayout(self.form)
        self.scroll_area = QtGui.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)
        self.scroll_content = QtGui.QWidget()
        self.scroll_layout = QtGui.QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(QtCore.Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        self.update_scan_list()

    def update_scan_list(self):
        from PySide import QtGui, QtCore
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        doc = FreeCAD.ActiveDocument
        if not doc:
            self.scroll_layout.addWidget(QtGui.QLabel("No scans loaded."))
            return
        
        mesh_objects = [obj for obj in doc.Objects if obj.isDerivedFrom("Mesh::Feature")]
        if not mesh_objects:
            self.scroll_layout.addWidget(QtGui.QLabel("No scans loaded."))
            return
            
        for obj in mesh_objects:
            row_layout = QtGui.QHBoxLayout()
            row_layout.addWidget(QtGui.QLabel(obj.Label))
            slider = QtGui.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(obj.ViewObject.Transparency)
            slider.valueChanged.connect(lambda value, o=obj.Name: self.set_transparency(o, value))
            row_layout.addWidget(slider)
            self.scroll_layout.addLayout(row_layout)
    
    def set_transparency(self, obj_name, value):
        doc = FreeCAD.ActiveDocument
        # This is the corrected line that removes the incompatible ':=' operator
        if doc:
            obj = doc.getObject(obj_name)
            if obj:
                obj.ViewObject.Transparency = value

class ImportScansCmd:
    """Command to import one or more STL scan files."""
    def Activated(self):
        from PySide import QtGui
        paths, _ = QtGui.QFileDialog.getOpenFileNames(None, "Select STL scans", "", "STL Files (*.stl)")
        if paths:
            doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("PatientCase")
            for path in paths:
                try:
                    import Mesh
                    Mesh.insert(path, doc.Name)
                except Exception as e:
                    print(f"Failed to import {path}: {e}")
            FreeCADGui.activeDocument().activeView().fitAll()
            if panel and FreeCADGui.Control.isDialogVisible(panel):
                panel.update_scan_list()

    def GetResources(self):
        return {'Pixmap': '', 'MenuText': 'Import Scans', 'ToolTip': 'Load patient STL files'}

class ShowPanelCmd:
    """Command to show or refresh the main control panel."""
    def Activated(self):
        global panel
        if panel and FreeCADGui.Control.isDialogVisible(panel):
            panel.update_scan_list()
        else:
            panel = DentaMindTaskPanel()
            FreeCADGui.Control.showDialog(panel)

    def GetResources(self):
        return {'Pixmap': '', 'MenuText': 'Show/Refresh Controls', 'ToolTip': 'Shows the main DentaMind AI control panel'}

class DentaMindAIWorkbench (Workbench):
    """The main DentaMind AI Workbench object."""
    MenuText = "DentaMind AI"
    ToolTip = "AI tools for dental design"
    Icon = ""

    def Initialize(self):
        self.toolbar = ["DentaMindAI_ImportScans", "DentaMindAI_ShowPanel"]
        self.appendToolbar("DentaMind AI Tools", self.toolbar)
        
    def Activated(self):
        print("DentaMind AI Workbench Activated.")

    def Deactivated(self):
        global panel
        if panel:
            FreeCADGui.Control.closeDialog(panel)
        print("DentaMind AI Workbench Deactivated.")

# --- 2. INITIALIZE AND REGISTER EVERYTHING AT THE END ---

panel = None # Global variable to hold the panel instance

FreeCADGui.addCommand('DentaMindAI_ImportScans', ImportScansCmd())
FreeCADGui.addCommand('DentaMindAI_ShowPanel', ShowPanelCmd())
FreeCADGui.addWorkbench(DentaMindAIWorkbench())