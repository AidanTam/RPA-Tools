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
uncapped_field=None
capped_field=None
domainf = None
weightf = None
inv_num = None
label = ""
unit = ""
out_stats = ""
out_settings = ""

st.title("Uncapped versus Capped Plot")


st.info('The influence of extreme values in an estimation domain is dependent on the values within each domain.'
        'THe uncapped versus capped plot is useful')
st.warning("this is a warning")
st.error("This is an error")
st.sidebar.markdown("## Parameters")


if st.sidebar.checkbox("Load Settings"):
    settings_files = common.get_dict_files("Capped vs Uncapped")
    settings_file = st.sidebar.selectbox("Stats Settings File", settings_files)
    settings_df = pd.read_csv(settings_file, index_col=0)
    # fill settings variables
    infile = settings_df.loc['Filename', 'Parameter']
    uncapped_field = settings_df.loc['Uncapped Field', 'Parameter']
    capped_field = settings_df.loc['Capped Field', 'Parameter']
    domainf = settings_df.loc['Domain Field', 'Parameter']
    weightf = settings_df.loc['Weight Field', 'Parameter']
    inv_num = settings_df.loc['Invalid Numbers', 'Parameter']
    label = settings_df.loc['Label', 'Parameter']
    unit = settings_df.loc['Unit', 'Parameter']
    out_stats = settings_df.loc['Stats File', 'Parameter']
    out_settings = settings_df.loc['Stats Settings', 'Parameter']


infiles = common.get_file_list([".csv", ".dm"])

if infile is not None:
    idx = common.get_idx(infiles, infile)
else:
    idx = 0

infile = st.sidebar.selectbox("Data File (.csv or .dm)", infiles, index=idx)

if infile != "--None--":

    df = common.load_file(infile)
    header = common.get_header(df)

    if uncapped_field is not None:
        idx = common.get_idx(header, uncapped_field)
    else:
        idx = 0

    uncapped_field = st.sidebar.selectbox("Uncapped Field", header, index=idx)

    if capped_field is not None:
        idx = common.get_idx(header, capped_field)
    else:
        idx = 0

    capped_field = st.sidebar.selectbox("Capped Field", header, index=idx)

    gradefields = [uncapped_field, capped_field]

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

    if gradefields[0] != "--None--" and gradefields[1] != "--None--" and domainf != "--None--":

        if inv_num is not None:
            idx = common.get_idx(['Ignore', 'Replace with Zero'], inv_num)
        else:
            idx = 0

        inv_num = st.sidebar.radio("Invalid Number Handling", ['Ignore', 'Replace with Zero'], index=idx)
        df_valid = common.invalid_number_handling(df, gradefields, inv_num)
        smp_obj = common.define_sample(df=df_valid, gradefields=gradefields, holeid="",
                                       xyzfields=['x', 'y', 'z'], domainf=domainf, weightf=weightf)
        pd.set_option('precision', 2)
        sortby = st.sidebar.radio("Sort Chart By:", ["Capped Grades", "Uncapped Grades"], key='sb')
        if sortby == "Capped Grades":
            sf = "capped"
        else:
            sf = "uncapped"

        label = st.sidebar.text_input("Plot Label", value=label)
        unit = st.sidebar.text_input("Display Unit", value=unit)

        smp_obj.capped_vs_uncapped_plot(cappedfield=capped_field, uncappedfield=uncapped_field, label=label, unit=unit, sortby=sf)
        st.pyplot()

        st.table(smp_obj.stats)

        if weightf != "--None--":
            st.markdown("*Statistics are weighted by " + weightf)
        else:
            st.markdown("*Statistics are unweighted")
        out_stats = st.sidebar.text_input("Save Statistics File", value=out_stats, key='t1')

        if ".csv" not in out_stats and out_stats!="":
            out_stats += ".csv"
        if st.sidebar.button("Save", key='b1'):
            smp_obj.stats.to_csv(out_stats, index=False)

        out_settings = st.sidebar.text_input("Save Settings File", value=out_settings, key='t2')

        if out_settings != "":
            if ".dict" not in out_settings:
                out_settings += ".dict"
            if st.sidebar.button("Save", key='b2'):
                index = ["Dict Type", "Filename", "Uncapped Field", "Capped Field", "Domain Field", "Weight Field",
                         "Invalid Numbers", "Label", "Unit", "Stats File", "Stats Settings"]
                settings = ['Capped vs Uncapped', infile, uncapped_field, capped_field, domainf, weightf, inv_num,
                            label, unit, out_stats, out_settings]
                pd.DataFrame({'Parameter': settings}, index=index).to_csv(out_settings)



