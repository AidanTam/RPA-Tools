import sys
from importlib import reload
import streamlit as st
from pyrpa.UI import common
import pandas as pd
import matplotlib.pyplot as plt
import pyrpa


if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding("utf-8")

@st.cache_data
def do_nothing():
    pass

infile = None
df = None
gradefield = None
xyzfields = []
domainf = None
rock1 = None
rock2 = None
inv_num = None
lagdist = 5.
numlags = 10
out_stats = ""
out_settings = ""

st.title("Contact Analysis")
st.info("**Contact plots** are generally used to observe boundary conditions between rock types or domains although they can"
        " also be used to test for bias in data sets e.g. underground chip versus channel data. "
        "The interpretation of the boundary conditions is useful for designing a sample search strategy during"
        " interpolation. ")
"""
Types of boundaries:
* Hard boundary - there is an **abrupt** change between the grades on either side of the contact
* Soft boundary - There is a **gradational** change in grade across the contact
* Transitional boundary - Near the contact there is a **steep** but **gradational** change in grade
"""

st.sidebar.markdown("## Parameters")

if st.sidebar.checkbox("Load Settings"):
    settings_files = common.get_dict_files("Contact Analysis")
    settings_file = st.sidebar.selectbox("Settings File", settings_files)
    settings_df = pd.read_csv(settings_file, index_col=0)
    # fill settings variables
    infile = settings_df.loc['Filename', 'Parameter']
    gradefield = settings_df.loc['Grade Field', 'Parameter']
    xyzfields = settings_df.loc['XYZ Fields', 'Parameter'].strip("][").split(', ')
    for i in range(len(xyzfields)):
        xyzfields[i] = xyzfields[i].strip("'")
    domainf = settings_df.loc['Domain Field', 'Parameter']
    rock1 = settings_df.loc['Rock 1', 'Parameter']
    rock2 = settings_df.loc['Rock 2', 'Parameter']
    inv_num = settings_df.loc['Invalid Numbers', 'Parameter']
    lagdist = settings_df.loc['Lag Distance', 'Parameter']
    numlags = settings_df.loc['Number of Lags', 'Parameter']
    out_settings = settings_df.loc['Settings', 'Parameter']


infiles = common.get_file_list([".csv", ".dm"])

if infile is not None:
    idx = common.get_idx(infiles, infile)
else:
    idx = 0

infile = st.sidebar.selectbox("Data File (.csv or .dm)", infiles, index=idx, key="s1")

if infile != "--None--":

    df = common.load_file(infile)
    header = common.get_header(df)

    if gradefield is not None:
        idx = common.get_idx(header, gradefield)
    else:
        idx = 0

    gradefield = st.sidebar.selectbox("Grade Field", header, index=idx, key="s2")

    if xyzfields == []:
        xyzfields = common.guess_field(header, 'xyzfields')
        if xyzfields is None:
            xyzfields = []

    xyzfields = st.sidebar.multiselect("XYZ Fields", header, xyzfields, key="m1")

    if domainf is not None:
        idx = common.get_idx(header, domainf)
    else:
        domainf = common.guess_field(header, 'domainf')
        if domainf is not None:
            idx = common.get_idx(header, domainf)
        else:
            idx = 0

    domainf = st.sidebar.selectbox("Domain Field", header, index=idx, key="s4")

    if domainf != "--None--":
        rocks = common.extend_list(list1=['--None--'], list2=df[domainf].unique())
        rocks = [str(i) for i in rocks]

        if rock1 is not None:
            idx = common.get_idx(rocks, rock1)
        else:
            idx = 0

        rock1 = st.sidebar.selectbox("Rock 1", rocks, index=idx)

        if rock2 is not None:
            idx = common.get_idx(rocks, rock2)
        else:
            idx = 0

        rock2 = st.sidebar.selectbox("Rock 2", rocks, index=idx)

        if gradefield != "--None--" and rock1 != '--None--' and rock2 != "--None--":

            if inv_num is not None:
                idx = common.get_idx(['Ignore', 'Replace with Zero'], inv_num)
            else:
                idx = 0

            inv_num = st.sidebar.radio("Invalid Number Handling", ['Ignore', 'Replace with Zero'], index=idx)
            df_valid = common.invalid_number_handling(df, [gradefield], inv_num)
            smp_obj = common.define_sample(df=df_valid, gradefields=[gradefield], holeid="",
                                           xyzfields=xyzfields, domainf=domainf, weightf=None)
            pd.set_option('precision', 2)
            try:
                rock1, rock2 = float(rock1), float(rock2)
            except:
                pass

            cnt_obj = pyrpa.contact_plot.contact_plot(smp_obj, gradefield)
            cnt_obj.fit(rock1, rock2)

            lagdist = st.sidebar.text_input("Lag Distance", lagdist)
            numlags = st.sidebar.text_input("Number of Lags", numlags)
            cnt_obj.plot(float(lagdist), int(numlags))
            st.pyplot()

            out_settings = st.sidebar.text_input("Save Settings File", value=out_settings)

            if out_settings != "":
                if ".dict" not in out_settings:
                    out_settings += ".dict"
                if st.sidebar.button("Save"):
                    index = ["Dict Type", "Filename", "Grade Field", "XYZ Fields", "Domain Field", "Rock 1", "Rock 2", "Invalid Numbers",
                    "Lag Distance", "Number of Lags", "Settings"]
                    settings = ['Contact Analysis', infile, gradefield, xyzfields, domainf, rock1, rock2, inv_num,
                                lagdist, numlags, out_settings]
                    pd.DataFrame({'Parameter': settings}, index=index).to_csv(out_settings)




