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
holeid = None
xyzfields = []
domainf = None
by_domain = None
num_neighbours = None
inv_num = None
outfile = ""
out_settings = ""

st.title("DDH Spacing")
st.sidebar.markdown("## Parameters")

if st.sidebar.checkbox("Load Settings"):
    settings_files = common.get_dict_files("DDH Spacing")
    settings_file = st.sidebar.selectbox("Settings File", settings_files)
    settings_df = pd.read_csv(settings_file, index_col=0)
    # fill settings variables
    infile = settings_df.loc['Filename', 'Parameter']
    holeid = settings_df.loc['Hole ID', 'Parameter']
    xyzfields = settings_df.loc['XYZ Fields', 'Parameter'].strip("][").split(', ')
    for i in range(len(xyzfields)):
        xyzfields[i] = xyzfields[i].strip("'")
    domainf = settings_df.loc['Domain Field', 'Parameter']
    by_domain = settings_df.loc['By Domain', 'Parameter']
    num_neighbours = settings_df.loc['Number of Neighbours', "Parameter"]
    outfile = settings_df.loc['Outfile', 'Parameter']
    out_settings = settings_df.loc['Settings', 'Parameter']


infile, df = common.upload_or_select([".csv", ".dm"], initial_value=infile)

if df is not None:
    header = common.get_header(df)

    if holeid is not None:
        idx = common.get_idx(header, holeid)
    else:
        idx = 0

    holeid = st.sidebar.selectbox("Hole ID", header, index=idx)

    xyzfields = st.sidebar.multiselect("XYZ Fields", header, xyzfields)

    if domainf is not None:
        idx = common.get_idx(header, domainf)
    else:
        idx = 0

    domainf = st.sidebar.selectbox("Domain Field", header, index=idx)

    if len(xyzfields) == 3 and holeid != "--None--":

        if inv_num is not None:
            idx = common.get_idx(['Ignore', 'Replace with Zero'], inv_num)
        else:
            idx = 0

        if domainf == "--None--":
            domainf = None
        else:
            by_domain = st.checkbox("Calculate Spacing by Domain", key='ch2')

        if num_neighbours is None:
            num_neighbours=3

        num_neighbours = int(num_neighbours)
        num_neighbours = st.number_input("Number of Nearest Drillholes to Use", min_value=1, max_value=10,
                                         value=num_neighbours, step=1)

        smp_obj = common.define_sample(df=df, gradefields=xyzfields, holeid=holeid,
                                       xyzfields=xyzfields, domainf=domainf, weightf=None)

        outfile = st.text_input("Save Output as (*.csv)", value=outfile)


        if st.button("Run and Save") and outfile != "":
            if ".csv" not in outfile:
                outfile += ".csv"
            with st.spinner("Calculating..."):
                smp_obj.spacing(nearest_neighbours=num_neighbours, by_domain=by_domain)

            smp_obj.data.to_csv(outfile, index=False)


        # st.pyplot()

        out_settings = st.sidebar.text_input("Save Settings File", value=out_settings)

        if out_settings != "":
            if ".dict" not in out_settings:
                out_settings += ".dict"
            if st.sidebar.button("Save"):
                index = ["Dict Type", "Filename", "Hole ID", "XYZ Fields", "Domain Field", "By Domain",
                         "Number of Neighbours", "Invalid Numbers", "Outfile", "Settings"]
                settings = ['DDH Spacing', infile, holeid, xyzfields, domainf, by_domain, num_neighbours, inv_num, outfile,
                            out_settings]
                pd.DataFrame({'Parameter': settings}, index=index).to_csv(out_settings)






