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
spacing = None
num_neighbours = None
inv_num = None
outfile = ""
out_settings = ""

common.show_header()
st.title("Thin DDH Spacing")
st.sidebar.markdown("## Parameters")

if st.sidebar.checkbox("Load Settings"):
    settings_files = common.get_dict_files("Thin DDH Spacing")
    settings_file = st.sidebar.selectbox("Settings File", settings_files)
    settings_df = pd.read_csv(settings_file, index_col=0)
    # fill settings variables
    infile = settings_df.loc['Filename', 'Parameter']
    holeid = settings_df.loc['Hole ID', 'Parameter']
    xyzfields = settings_df.loc['XYZ Fields', 'Parameter'].strip("][").split(', ')
    for i in range(len(xyzfields)):
        xyzfields[i] = xyzfields[i].strip("'")
    spacing = settings_df.loc['Spacing', "Parameter"]
    num_neighbours = settings_df.loc['Number of Neighbours', "Parameter"]
    outfile = settings_df.loc['Outfile', 'Parameter']
    out_settings = settings_df.loc['Settings', 'Parameter']


infile, df = common.upload_or_select([".csv", ".dm"], initial_value=infile)

if df is not None:
    header = common.get_header(df)

    if holeid is not None:
        idx = common.get_idx(header, holeid)
    else:
        holeid = common.guess_field(header)
        if holeid is not None:
            idx = common.get_idx(header, holeid)
        else:
            idx = 0

    holeid = st.sidebar.selectbox("Hole ID", header, index=idx)

    if xyzfields == []:
        xyzfields = common.guess_field(header, 'xyzfields')
        if xyzfields is None:
            xyzfields = []

    xyzfields = st.sidebar.multiselect("XYZ Fields", header, xyzfields)

    if spacing is None:
        spacing = 10.

    spacing = st.number_input("Thin Spacing", value=spacing)

    if len(xyzfields) == 3 and holeid != "--None--":

        if inv_num is not None:
            idx = common.get_idx(['Ignore', 'Replace with Zero'], inv_num)
        else:
            idx = 0

        if num_neighbours is None:
            num_neighbours=3

        num_neighbours = int(num_neighbours)
        num_neighbours = st.number_input("Number of Nearest Drillholes to Use", min_value=1, max_value=10,
                                         value=num_neighbours, step=1)

        smp_obj = common.define_sample(df=df, gradefields=xyzfields, holeid=holeid,
                                       xyzfields=xyzfields, domainf=None, weightf=None)
        with st.spinner("Calculating DDH Spacing..."):
            smp_obj.spacing(nearest_neighbours=num_neighbours)
            plt.hist(smp_obj.data._spacing)
            plt.xlabel('Spacing')
            plt.ylabel('Count')
            st.pyplot()

        outfile = st.text_input("Save Output as (*.csv)", value=outfile)

        if st.button("Run and Save") and outfile != "":
            if ".csv" not in outfile:
                outfile += ".csv"
            with st.spinner("Calculating..."):
                smp_obj.thin_ddh_spacing(target_spacing=spacing, nearest_neighbours=num_neighbours)

            smp_obj.data.to_csv(outfile, index=False)


        # st.pyplot()

        out_settings = st.sidebar.text_input("Save Settings File", value=out_settings)

        if out_settings != "":
            if ".dict" not in out_settings:
                out_settings += ".dict"
            if st.sidebar.button("Save"):
                index = ["Dict Type", "Filename", "Hole ID", "XYZ Fields", "Spacing",
                         "Number of Neighbours", "Invalid Numbers", "Outfile", "Settings"]
                settings = ['Thin DDH Spacing', infile, holeid, xyzfields, spacing, num_neighbours, inv_num, outfile,
                            out_settings]
                pd.DataFrame({'Parameter': settings}, index=index).to_csv(out_settings)






