import streamlit as st
import pyvista as pv
from stpyvista import stpyvista
import open3d as o3d
import google.generativeai as genai
import os
import numpy as np

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="DentaMind AI Designer")

# --- Helper Function to Prepare Mesh Data for AI ---
def get_mesh_summary(mesh_file):
    """Reads an STL file and returns a summary for the AI."""
    mesh = o3d.io.read_triangle_mesh(mesh_file)
    num_vertices = len(mesh.vertices)
    bounding_box = mesh.get_axis_aligned_bounding_box()
    center = bounding_box.get_center()
    size = bounding_box.get_extent()
    
    summary = (
        f"Mesh Summary:\n"
        f"- Vertices: {num_vertices}\n"
        f"- Bounding Box Center: {np.round(center, 2)}\n"
        f"- Bounding Box Size: {np.round(size, 2)}\n"
    )
    return summary

# --- Main UI ---
st.title("DentaMind AI 🦷 Designer")
st.write("Upload scans, describe the desired design, and let the AI assist you.")

# Create a layout with a main viewer and a side control panel.
viewer_col, control_col = st.columns([3, 1])

with control_col:
    st.header("Controls")
    
    # --- API Key and Model Setup ---
    api_key = st.text_input("Enter your Google Gemini API Key:", type="password")
    model = None
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            st.success("Gemini API Connected.")
        except Exception as e:
            st.error(f"API Error: {e}")

    # --- File Uploaders ---
    prep_scan_file = st.file_uploader("1. Preparation Scan")
    opp_scan_file = st.file_uploader("2. Opposing Arch Scan")
    
    st.divider()

    # --- AI Prompt Input ---
    design_prompt = st.text_area(
        "Describe the design...",
        height=150,
        placeholder="e.g., 'Generate a full contour wax-up for the prepared central incisor. Ensure good contact with adjacent teeth and check occlusion.'"
    )
    
    generate_button = st.button("✨ Generate Design")

with viewer_col:
    st.header("3D Workspace")
    plotter = pv.Plotter(window_size=[1000, 800], border=False)
    
    # Save uploaded files temporarily to be read by PyVista and Open3D
    if prep_scan_file:
        with open("temp_prep.stl", "wb") as f:
            f.write(prep_scan_file.getbuffer())
        prep_mesh_pv = pv.read("temp_prep.stl")
        plotter.add_mesh(prep_mesh_pv, color='#FFFFFF', smooth_shading=True, name="prep_mesh")

    if opp_scan_file:
        with open("temp_opp.stl", "wb") as f:
            f.write(opp_scan_file.getbuffer())
        opp_mesh_pv = pv.read("temp_opp.stl")
        plotter.add_mesh(opp_mesh_pv, color='#6194FF', smooth_shading=True, name="opp_mesh")
    
    plotter.view_isometric()
    stpyvista(plotter, key="pv_viewer")

# --- AI Generation Logic ---
if generate_button:
    if not model:
        st.error("Please enter a valid Gemini API key to generate a design.")
    elif not prep_scan_file or not opp_scan_file:
        st.error("Please upload both preparation and opposing scans.")
    elif not design_prompt:
        st.error("Please describe the design you want.")
    else:
        with st.spinner("Connecting to DentaMind AI... Analyzing scans and generating design..."):
            # 1. Get summaries of the 3D meshes.
            prep_summary = get_mesh_summary("temp_prep.stl")
            opp_summary = get_mesh_summary("temp_opp.stl")

            # 2. Construct a detailed prompt for the Gemini API.
            full_prompt = (
                "You are an expert dental CAD designer. Your task is to provide the design parameters for a dental restoration based on the user's request and scan data.\n\n"
                f"**User Request:**\n{design_prompt}\n\n"
                f"**Preparation Scan Data:**\n{prep_summary}\n\n"
                f"**Opposing Arch Scan Data:**\n{opp_summary}\n\n"
                "Based on all this information, provide a structured list of design steps and parameters for the restoration. Do not generate the 3D model itself, but provide the instructions for a CAD program to follow."
            )
            
            # 3. Send the prompt to Gemini.
            try:
                response = model.generate_content(full_prompt)
                
                # 4. Display the AI's response.
                st.success("AI has generated a design plan!")
                with st.expander("View AI Design Parameters"):
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"An error occurred while communicating with the AI: {e}")