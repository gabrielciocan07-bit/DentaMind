bl_info = {
    "name": "DentaMind AI",
    "author": "Your Name",
    "version": (1, 10),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > DentaMind AI",
    "description": "AI-assisted tools for dental design.",
    "category": "3D View",
}

import bpy
import os
# ... (bl_info dictionary) ...
import bpy
import os
import numpy as np # Keep numpy import if needed elsewhere


# --- Helper Function for AI Setup ---
# ... (rest of your script remains the same) ...
import numpy as np

# --- Helper Function for AI Setup ---
gemini_model = None
bpy.types.Scene.dentamind_api_status = bpy.props.StringProperty(name="API Status", default="Not Set")

def setup_gemini_on_update(self, context):
    """Callback function triggered when the API key property changes."""
    # --- THIS IS THE FIX ---
    # Declare 'global' at the very beginning of the function
    global gemini_model

    api_key = self.api_key
    if not api_key:
        context.scene.dentamind_api_status = "Not Set"
        gemini_model = None # Reset the model if key is cleared
        print("API Key cleared.")
        return

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel('gemini-1.5-pro-latest')
        context.scene.dentamind_api_status = "Connected"
        print("Gemini API Connected Successfully.")
    except ImportError:
        context.scene.dentamind_api_status = "Error: google-generativeai library missing."
        print(context.scene.dentamind_api_status)
        gemini_model = None
    except Exception as e:
        context.scene.dentamind_api_status = f"API Error: {e}"
        print(context.scene.dentamind_api_status)
        gemini_model = None

def get_mesh_summary(obj):
    """Creates a text summary of a mesh object for the AI."""
    if not obj or obj.type != 'MESH': return "Not a valid mesh object."
    mesh = obj.data
    verts = np.array([v.co for v in mesh.vertices])
    if not verts.any(): return f"Mesh Summary ({obj.name}): Empty"
    min_coords, max_coords = np.min(verts, axis=0), np.max(verts, axis=0)
    center, size = (min_coords + max_coords) / 2.0, max_coords - min_coords
    return f"Mesh Summary ({obj.name}): Verts={len(mesh.vertices)}, Center={np.round(center, 2)}, Size={np.round(size, 2)}"

# --- Operator 1: Import Scans ---
class DENTAMIND_OT_import_scans(bpy.types.Operator):
    """Imports STLs and sets them up."""
    bl_label = "Import Scans"
    bl_idname = "dentamind.import_scans"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        if "Cube" in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)

        folder = os.path.dirname(self.filepath)
        imported_objects = []
        for f in self.files:
            objects_before = set(bpy.data.objects)
            bpy.ops.wm.stl_import(filepath=os.path.join(folder, f.name))
            new_objects = set(bpy.data.objects) - objects_before
            imported_objects.extend(list(new_objects))

        for obj in imported_objects:
            if obj.type == 'MESH':
                if not obj.active_material:
                    mat = bpy.data.materials.new(name=f"{obj.name}_Mat")
                    obj.active_material = mat
                    mat.use_nodes = True
                    mat.blend_method = 'BLEND'
                principled = mat.node_tree.nodes.get("Principled BSDF")
                if principled:
                    color = (0.8, 0.8, 0.8, 1)
                    if 'lower' in obj.name.lower(): color = (0.3, 0.5, 1, 1)
                    principled.inputs['Base Color'].default_value = color
        
        for area in context.screen.areas:
             if area.type == 'VIEW_3D': area.tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# --- Operator 2: Generate Design ---
class DENTAMIND_OT_generate_design(bpy.types.Operator):
    """Sends scan info and prompt to Gemini API."""
    bl_label = "Generate AI Design Plan"
    bl_idname = "dentamind.generate_design"

    def execute(self, context):
        global gemini_model
        scene = context.scene
        if not hasattr(scene, "dentamind_props"): return {'CANCELLED'}
        props = scene.dentamind_props

        if not gemini_model or context.scene.dentamind_api_status != "Connected":
            self.report({'ERROR'}, "Gemini API not connected.")
            return {'CANCELLED'}

        meshes = [obj for obj in scene.objects if obj.type == 'MESH']
        if not meshes: self.report({'ERROR'}, "No scans loaded."); return {'CANCELLED'}
        if not props.ai_prompt: self.report({'ERROR'}, "Please enter a design prompt."); return {'CANCELLED'}

        mesh_summaries = "\n".join([get_mesh_summary(obj) for obj in meshes])
        full_prompt = f"Expert dental CAD designer request:\n{props.ai_prompt}\n\nScan Data:\n{mesh_summaries}\n\nProvide design steps/parameters."

        try:
            self.report({'INFO'}, "Sending request to Gemini AI...")
            response = gemini_model.generate_content(full_prompt)
            print("\n--- DentaMind AI Response ---\n", response.text, "\n--- End Response ---\n")
            self.report({'INFO'}, "AI response received. Check System Console.")
        except Exception as e:
            error_message = f"Error communicating with AI: {e}"
            print(error_message)
            self.report({'ERROR'}, error_message)
            return {'CANCELLED'}
        return {'FINISHED'}

# --- Blender Properties Group ---
class DentaMindProperties(bpy.types.PropertyGroup):
    api_key: bpy.props.StringProperty(
        name="Gemini API Key", subtype='PASSWORD',
        description="Enter your Google Gemini API Key. Press Enter to connect.",
        update=setup_gemini_on_update
    )
    ai_prompt: bpy.props.StringProperty(name="AI Prompt", subtype='BYTE_STRING', default="Generate a wax-up.")

# --- The Custom UI Panel ---
class DENTAMIND_PT_main_panel(bpy.types.Panel):
    bl_label = "DentaMind AI"
    bl_idname = "DENTAMIND_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DentaMind AI'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        if not hasattr(scene, "dentamind_props"): return
        props = scene.dentamind_props

        box = layout.box()
        box.label(text="Patient Setup")
        box.operator("dentamind.import_scans", icon='IMPORT')

        box = layout.box()
        box.label(text="Scene Objects")
        mesh_objects = [obj for obj in scene.objects if obj.type == 'MESH']
        if not mesh_objects: box.label(text="No scans loaded.")
        for obj in mesh_objects:
            if obj.active_material and obj.active_material.use_nodes and obj.active_material.node_tree:
                principled = obj.active_material.node_tree.nodes.get("Principled BSDF")
                if principled and 'Alpha' in principled.inputs:
                     box.prop(principled.inputs['Alpha'], "default_value", text=obj.name, slider=True)

        box = layout.box()
        box.label(text="AI Assistant")
        box.prop(props, "api_key")
        box.label(text=f"Status: {scene.dentamind_api_status}")
        box.prop(props, "ai_prompt", text="")
        row = box.row()
        row.enabled = (gemini_model is not None and scene.dentamind_api_status == "Connected")
        row.operator("dentamind.generate_design", icon='LIGHT')

# --- Registration ---
classes = ( DENTAMIND_OT_import_scans, DENTAMIND_OT_generate_design, DentaMindProperties, DENTAMIND_PT_main_panel )

def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.dentamind_props = bpy.props.PointerProperty(type=DentaMindProperties)
    bpy.types.Scene.dentamind_api_status = bpy.props.StringProperty(name="API Status", default="Not Set")
    print("DentaMind AI Add-on Registered.")

def unregister():
    if hasattr(bpy.types.Scene, "dentamind_props"): del bpy.types.Scene.dentamind_props
    if hasattr(bpy.types.Scene, "dentamind_api_status"): del bpy.types.Scene.dentamind_api_status
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
    print("DentaMind AI Add-on Unregistered.")

if __name__ == "__main__":
    register()