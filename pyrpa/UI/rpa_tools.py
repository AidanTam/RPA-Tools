import sys
from importlib import reload
import streamlit as st
import os
from PIL import Image

if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding("utf-8")

path = os.path.dirname(__file__)

st.set_page_config(page_title="SLR Celest RPA Tools", layout="wide")

logo = Image.open(os.path.join(path, 'logo-slr-2018.png'))
st.sidebar.image(logo, caption='')
logo = Image.open(os.path.join(path, 'Celest.png'))
st.sidebar.image(logo, caption='')

st.title("SLR Celest Resource Estimation Tools")
st.markdown("A collection of miraculous tools for resource geologists.")
st.markdown("**Version 1.0.2**")
st.markdown("Select a tool from the sidebar to get started.")

image = Image.open(os.path.join(path, 'gibraltar_0857.jpg'))
st.image(image, caption='', use_column_width=True)
