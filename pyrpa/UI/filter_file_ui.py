import streamlit as st
import pandas as pd
from pyrpa.UI import common

@st.cache
def do_nothing():
    pass

st.markdown("# File Filter")

infiles = common.get_file_list([".csv", ".dm"])

infile = st.selectbox("Filename", infiles)

if infile != "--None--":

    df_in = common.load_file(infile)
    df = df_in.copy()
    header = common.get_header(df_in)
    st.sidebar.write("File contains " + str(len(df)) + " records:")
    if st.sidebar.checkbox("Categories to Keep"):
        fname = st.selectbox("Field to Filter on:", header)
        if fname != "--None--":
            fvalues = df[fname].unique()
            fval_list = st.multiselect("Select Values to Keep:", fvalues, [])
            df = df[df[fname].isin(fval_list)]
            st.write("File contains " + str(len(df)) + " records:")

    if st.checkbox("Filter 2"):
        fname2 = st.selectbox("Field to Filter on:", header)
        if fname2 != "--None--":
            fvalues2 = df[fname2].unique()
            fval_list2 = st.multiselect("Select Values to Keep:", fvalues2, [])
            df = df[df[fname2].isin(fval_list2)]
            st.write("File contains " + str(len(df)) + " records:")

        outfile = st.text_input("Save File As:")

        if st.button("Save"):
            df.to_csv(outfile, index=False)