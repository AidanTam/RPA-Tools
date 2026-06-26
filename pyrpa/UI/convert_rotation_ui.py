import transforms3d
import numpy as np
import streamlit as st

st.markdown("# Convert between different rotation convertions")

rotations = ['szxz', 'szxy']

input_convention = st.selectbox("Input Rotation Convention", options=rotations, index=0, key='inp_cov')
rot1 = st.number_input(label="Rotation 1", min_value=-360., max_value=360., value=0., key='r1')
rot2 = st.number_input(label="Rotation 2", min_value=-360., max_value=360., value=0., key='r2')
rot3 = st.number_input(label="Rotation 3", min_value=-360., max_value=360., value=0., key='r3')
output_convention = st.selectbox("Output Rotation Convention", options=rotations, index=0, key='inp_cov')

mat = transforms3d.euler.euler2mat(ai=np.radians(rot1), aj=np.radians(rot2), ak=np.radians(rot3), axes=input_convention)
ai, aj, ak = transforms3d.euler.mat2euler(mat, axes=output_convention)
st.write("")
st.write("")
st.markdown("## Output:")
st.write("Output angles for " + output_convention)
st.write("Rotation 1 = " + str(np.round(np.degrees(ai),4)))
st.write("Rotation 2 = " + str(np.round(np.degrees(aj),4)))
st.write("Rotation 3 = " + str(np.round(np.degrees(ak),4)))