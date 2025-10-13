import FreeCAD, FreeCADGui

class DentaMindAIWorkbench (Workbench):
    "DentaMind AI Workbench object"

    MenuText = "DentaMind AI"
    ToolTip = "AI tools for dental design"
    Icon = ""

    def Initialize(self):
        """This function is executed when the workbench is activated."""
        
        class ImportScansCmd:
            def Activated(self):
                """This runs when the button is clicked."""
                from PySide import QtGui
                
                file_paths, _ = QtGui.QFileDialog.getOpenFileNames(
                    None, 
                    "Select patient STL scans", 
                    "", 
                    "STL Files (*.stl)"
                )
                
                if file_paths:
                    doc = FreeCAD.activeDocument()
                    if not doc:
                        doc = FreeCAD.newDocument("PatientCase")
                    
                    for path in file_paths:
                        try:
                            # --- THIS IS THE CORRECTED PART ---
                            # Use the Mesh module, which is designed for STL files.
                            import Mesh
                            Mesh.insert(path, doc.Name)
                            print(f"Successfully imported: {path}")
                        except Exception as e:
                            print(f"Failed to import {path}: {e}")
                    
                    FreeCADGui.activeDocument().activeView().fitAll()

            def GetResources(self):
                """Defines the button's appearance."""
                return {'Pixmap'  : '',
                        'MenuText': 'Import Case Scans',
                        'ToolTip' : 'Load patient STL files into the current document'}

        FreeCADGui.addCommand('DentaMindAI_ImportScans', ImportScansCmd())

        self.toolbar = ["DentaMindAI_ImportScans"]
        self.appendToolbar("DentaMind AI Tools", self.toolbar)
        
        print("DentaMind AI Workbench Initialized with Mesh Import tool.")

    def Activated(self):
        print("DentaMind AI Workbench Activated.")

    def Deactivated(self):
        print("DentaMind AI Workbench Deactivated.")

FreeCADGui.addWorkbench(DentaMindAIWorkbench())