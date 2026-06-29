import streamlit as st
import pandas as pd
import os
import numpy as np
st.set_page_config(layout="wide")

if 'skipped' not in st.session_state:
    st.session_state['skipped'] = None

if 'mergeddf' not in st.session_state:
    st.session_state['mergeddf'] = pd.DataFrame({})


if 'assaydf' not in st.session_state:
    st.session_state['assaydf'] = pd.DataFrame({})

if 'analysisdf' not in st.session_state:
    st.session_state['analysisdf'] = pd.DataFrame({})

if 'filter' not in st.session_state:
    st.session_state['filter'] = []

if 'unique' not in st.session_state:
    st.session_state['unique'] = []

def Merge():
    st.session_state.mergeddf= pd.concat(dataframes, axis=0)
    st.session_state.filter = st.session_state.mergeddf.columns

def ChangedCol():
    st.session_state.unique = st.session_state.mergeddf[Columns].unique()


def Filter():
    st.session_state.mergeddf = st.session_state.mergeddf[st.session_state.mergeddf[Columns].isin(uniquevalues)]

def DelCol():
    st.session_state.mergeddf = st.session_state.mergeddf[colstokeep]
    st.session_state.filter = st.session_state.mergeddf.columns

def replace_values(value):
    if isinstance(value, str) and value.startswith('>'):
        return float(value[1:])
    elif isinstance(value, str) and value.startswith('<'):
        return float(value[1:]) / 2
    else:
        return value

def replace_detection_limits():
    st.session_state.mergeddf = st.session_state.mergeddf.map(replace_values)

dataframes = []
elementdf = {}
with st.sidebar:
    uploaded_file = st.file_uploader("Certificates to Merge",accept_multiple_files=True)
    if uploaded_file is not None:
        filenames = [i.name for i in uploaded_file ]
        files = [i for i in uploaded_file ]


    
    filetocheck = st.selectbox('Select a File to check',filenames)
    HeaderRows = st.number_input('Number of Header Rows',min_value=1, max_value=99, value=1, step=1)
    Headerkeywrod = st.text_input('Header Keyword', 'Method')
    RowsToSkip = st.number_input('Rows to Skip',min_value=0, max_value=None, value=0, step=1)

    Merge_button = st.button(label='Merge Files', on_click=Merge)
    detectionlimit = st.checkbox('Convert Detection Limit Values')
    colstokeep = st.multiselect('Choose Columns', st.session_state.filter)

    filter_button = st.button(label='Keep Selected', on_click=DelCol)    
    
    Columns = st.selectbox('Filter Data',st.session_state.filter)
    uniquevalues = st.multiselect('Filter by Values', st.session_state.unique)


    update_values = st.button(label='Update Values',on_click = ChangedCol)
    filter_button = st.button(label='Filter Results', on_click=Filter)
    assay_file = st.file_uploader("Upload Assay File",accept_multiple_files=False)
    certcols = st.multiselect('Certif. Columns to keep', st.session_state.filter)
    assaycols = st.multiselect('Assay Columns to keep', st.session_state.assaydf.columns)
    if assay_file is not None:
        st.session_state.assaydf = pd.read_csv(assay_file)
    Elements = [k for k in range(st.number_input('Number of Element', min_value=1, value=1, step=1))]

certelements = []
assayelements = []
col1, col2 = st.columns(2)
with col1:
    st.header('Certificate')
    certif_sample = st.selectbox('Certif.Sample Field', st.session_state.filter)
    for i in Elements:
        c_element = st.selectbox('C-Element ' + str(i), st.session_state.filter)
        certelements.append(c_element)
with col2:
    st.header('Assay')
    assay_sample = st.selectbox('Assay Sample Field', st.session_state.assaydf.columns)
    for j in Elements:
        a_element = st.selectbox('A-Element ' + str(j), st.session_state.assaydf.columns)
        assayelements.append(a_element)



# merged_df = None    
with st.expander("Data Checker"):
    if not filenames or filetocheck is None:
        st.info('Please upload certificate files to preview.')
    else:
        try:
            index = filenames.index(filetocheck)
            byte_data = files[index].getvalue()
            string_data = byte_data.decode('utf-8')
            lines = string_data.splitlines()
            for i, line in enumerate(lines):
                header_row = None
                if Headerkeywrod in line:
                    header_row = i-1
                    if header_row == -1:
                        header_row = 0
                    break
            st.write(str(header_row) + ' Rows Skipped')
            st.session_state.skipped = [i for i in range(header_row)]
            st.session_state.skipped.append(RowsToSkip)
            df = pd.read_csv(files[index], skiprows=st.session_state.skipped, header=[i for i in range(HeaderRows)])
            df = df.dropna(how='all')
            st.dataframe(df)
        except Exception as e:
            st.error(f'Error reading file: {e}')


with st.expander("Merged Table"):
    for k in files:
        fileindex = files.index(k)
        try:
            df2 = pd.read_csv(k,skiprows=st.session_state.skipped, header=[i for i in range(HeaderRows)])
            df2.columns = ['_'.join(col).strip() for col in df2.columns.values]
            df2['Filename'] = filenames[fileindex]
            dataframes.append(df2)
            if detectionlimit:
                replace_detection_limits()
            else:
                Merge()
        except:
            pass
    st.dataframe(st.session_state.mergeddf)
    st.download_button(
                        label="Download Merged Certificates",
                        data=st.session_state.mergeddf.to_csv().encode('utf-8'),
                        file_name='Merged Certificates.csv',
                        mime='text/csv',
                            )

with st.expander("Assay Table"):
    st.dataframe(st.session_state.assaydf)


with st.expander("Analysis"):
    if st.session_state.mergeddf.empty or st.session_state.assaydf.empty:
        st.info('Merge certificate files and upload an assay file to run analysis.')
    else:
        try:
            for celm, aelem in zip(certelements, assayelements):
                st.session_state.analysisdf = st.session_state.mergeddf[certcols+[celm]].merge(st.session_state.assaydf[assaycols+[aelem]], left_on=certif_sample, right_on=assay_sample)
                st.session_state.analysisdf[celm] = st.session_state.analysisdf[celm].astype('float64')
                st.session_state.analysisdf[aelem] = st.session_state.analysisdf[aelem].astype('float64')
                st.session_state.analysisdf = st.session_state.analysisdf.dropna(subset=[celm, aelem], how='any')
                st.session_state.analysisdf['Difference'] = abs(st.session_state.analysisdf[celm]-st.session_state.analysisdf[aelem])
                st.dataframe(st.session_state.analysisdf)
                elementdf.update({aelem: st.session_state.analysisdf})
                st.download_button(
                    label="Download data as CSV",
                    data=st.session_state.analysisdf.to_csv().encode('utf-8'),
                    file_name=aelem+'_verif.csv',
                    mime='text/csv',
                )
        except Exception as e:
            st.error(f'Analysis error: {e}')

with st.expander("Reporting"):
    col3,col4 = st.columns(2)
    for elem, dfs in elementdf.items():
        difference_count = dfs[dfs['Difference'] > 0].shape[0]
        if difference_count == 0:
            col3.success('There are 0 differences in '+elem, icon="✅")
        else:
            col3.warning('There are '+ str(difference_count)+' errors in '+ elem)


