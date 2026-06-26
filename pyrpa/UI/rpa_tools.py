import sys
from importlib import reload
import streamlit as st
import os
import numpy as np
import glob
import pandas as pd
import pyrpa
import subprocess
from PIL import Image
import matplotlib.pyplot as plt

if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding("utf-8")

cwd = os.getcwd()

@st.cache
def do_nothing():
    pass


# path = os.getcwd()
path = os.path.dirname(__file__)

def streamlit_run(module):
    subprocess.check_call(["powershell.exe", "streamlit run " + path + "\\" + module], shell=True)

logo = Image.open(path + "\\" + 'logo-slr-2018.png')
st.sidebar.image(logo, caption='')
# st.sidebar.title("# Product Name")
logo = Image.open(path + "\\" + 'Celest.png')
st.sidebar.image(logo, caption='')

prog_options = ["Home", "Plotting Tools", "Sample Tools", "Block Model Tools", "Geostats Tools", "QA/QC","Data Validation"]
prog_radio = st.sidebar.radio("", prog_options)

if prog_radio == prog_options[0]:
    '''
    # SLR Celest Resource Estimation Tools
    
    A collection of miraculous tools for resource geologists.
    '''
    st.markdown('Version 1.0.2')
    image = Image.open(path + "\\" + 'gibraltar_0857.jpg')
    st.image(image, caption='', use_column_width=True)

if prog_radio == prog_options[1]:
    st.markdown("## Plotting Tools:")
    # if st.button("Filter File"):
    #     streamlit_run(module="filter_file_ui.py")
    if st.button("Box Plot"):
        streamlit_run(module="box_plot_ui.py")
    if st.button("Scatter Plot"):
        streamlit_run(module="scatter_plot_ui.py")
    if st.button("Width Plot"):
        streamlit_run(module="width_plot_ui.py")


if prog_radio == prog_options[2]:
    st.markdown("## Sample Tools:")


    if st.button("Statistics"):
        streamlit_run(module="sample_stats_ui.py")

    # if st.button("Capping Analysis"):
    #     streamlit_run(module="capping_ui.py")

    if st.button("Capping Analysis"):
        streamlit_run(module="capping_ui_v2.py")

    if st.button("Uncapped vs Capped Plot"):
        streamlit_run(module="capped_vs_uncapped_plot_ui.py")

    if st.button("Contact Analysis"):
        streamlit_run(module="contact_plot_ui.py")

    if st.button("Calculate DDH Spacing"):
        streamlit_run(module="ddh_spacing_ui.py")

    if st.button("Thin DDH Spacing"):
        streamlit_run(module="thin_ddh_spacing_ui.py")

if prog_radio == prog_options[3]:
    '''
    # Block Model Tools:
    
    Collection of Block Model Tools
    
    '''

    if st.checkbox("Reporting"):

        if st.button("Resource Report"):
            pass

        if st.button("Statistics"):
            pass

        if st.button("GT Curve"):
            pass

    if st.checkbox("Block Model Validation"):

        if st.button("Convert Rotations (between conventions)"):
            streamlit_run(module="convert_rotation_ui.py")

        if st.button("Compare Means"):
            pass

        if st.button("Swath Plot"):
            pass

        if st.button("Global Change of Support Check"):
            pass

    if st.checkbox("Post-Processing"):

        if st.button("Reblock"):
            pass

        if st.button("Label Connected Blocks"):
            pass

        if st.button("Categorical Smoothing"):
            pass

        if st.button("Smart Dilution"):
            pass


if prog_radio == prog_options[4]:
    st.markdown("## Geostats Tools:")

    if st.button("Gammabar Plot"):
        streamlit_run(module="gammabar_ui.py")

if prog_radio == prog_options[5]:
    st.markdown("## QA/QC Tools:")

    if st.button("Standards"):
        pass

    if st.button("Blanks"):
        pass

    if st.button("Duplicates"):
        pass



if prog_radio == prog_options[6]:
    st.markdown("## Data Validation ")

    if st.button("Data Verification tool"):
        streamlit_run(module="data_verification_ui.py")
        pass

    if st.button("Drill Hole Comparison"):
        streamlit_run(module="Get_Nearest_ui.py")
        pass








