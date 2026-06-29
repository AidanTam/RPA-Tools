import sys
from importlib import reload
import streamlit as st
from pyrpa.UI import common
import pandas as pd
import matplotlib.pyplot as plt


if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding("utf-8")

@st.cache_data
def do_nothing():
    pass

infile = None
df = None
gradefields = []
domainf = None
weightf = None
inv_num = None
out_stats = ""
out_settings = ""

st.title("Sample Statistics")
st.sidebar.markdown("## Parameters")

if st.sidebar.checkbox("Load Settings"):
    stats_settings_files = common.get_dict_files("Sample Statistics")
    stats_settings_file = st.sidebar.selectbox("Stats Settings File", stats_settings_files)
    stats_settings_df = pd.read_csv(stats_settings_file, index_col=0)
    # fill settings variables
    infile = stats_settings_df.loc['Filename', 'Parameter']
    gradefields = stats_settings_df.loc['Grade Fields', 'Parameter'].strip("][").split(', ')
    for i in range(len(gradefields)):
        gradefields[i] = gradefields[i].strip("'")
    domainf = stats_settings_df.loc['Domain Field', 'Parameter']
    weightf = stats_settings_df.loc['Weight Field', 'Parameter']
    inv_num = stats_settings_df.loc['Invalid Numbers', 'Parameter']
    out_stats = stats_settings_df.loc['Stats File', 'Parameter']
    out_settings = stats_settings_df.loc['Stats Settings', 'Parameter']


infile, df = common.upload_or_select([".csv", ".dm"], initial_value=infile)

if df is not None:
    header = common.get_header(df)

    gradefields = st.sidebar.multiselect("Grade Fields", header, gradefields)

    if domainf is not None:
        idx = common.get_idx(header, domainf)
    else:
        idx = 0

    domainf = st.sidebar.selectbox("Domain Field", header, index=idx)

    if weightf is not None:
        idx = common.get_idx(header, weightf)
    else:
        idx = 0

    weightf = st.sidebar.selectbox("Weight Field", header, index=idx)

    if len(gradefields)>0:

        if inv_num is not None:
            idx = common.get_idx(['Ignore', 'Replace with Zero'], inv_num)
        else:
            idx = 0

        inv_num = st.sidebar.radio("Invalid Number Handling", ['Ignore', 'Replace with Zero'], index=idx)
        df_valid = common.invalid_number_handling(df, gradefields, inv_num)
        smp_obj = common.define_sample(df=df_valid, gradefields=gradefields, holeid="",
                                       xyzfields=['x', 'y', 'z'], domainf=domainf, weightf=weightf)
        pd.set_option('precision', 2)
        st.table(smp_obj.stats)
        if weightf != "--None--":
            st.markdown("*Statistics are weighted by " + weightf)
        else:
            st.markdown("*Statistics are unweighted")
        out_stats = st.sidebar.text_input("Save Statistics File", value=out_stats)

        if ".csv" not in out_stats:
            out_stats += ".csv"
        if st.sidebar.button("Save", key="save1"):
            smp_obj.stats.to_csv(out_stats, index=False)

        out_settings = st.sidebar.text_input("Save Settings File", value=out_settings)

        if out_settings != "":
            if ".dict" not in out_settings:
                out_settings += ".dict"
            if st.sidebar.button("Save", key="save2"):
                index = ["Dict Type", "Filename", "Grade Fields", "Domain Field", "Weight Field",
                         "Invalid Numbers", "Stats File", "Stats Settings"]
                settings = ['Sample Statistics', infile, gradefields, domainf, weightf, inv_num, out_stats, out_settings]
                pd.DataFrame({'Parameter': settings}, index=index).to_csv(out_settings)


        if domainf != "--None--":

            for gf in gradefields:
                filt = smp_obj.stats.Variable == gf
                plt.plot(smp_obj.stats.Average[filt], smp_obj.stats.CV[filt], 'o')
            plt.title("Mean versus CV Plot")
            plt.legend(gradefields, loc="best", borderaxespad=0)
            plt.xlabel("Mean")
            plt.ylabel("CV")
            st.pyplot()

