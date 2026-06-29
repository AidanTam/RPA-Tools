import glob
import pyrpa
import pandas as pd
import streamlit as st
import os
from PIL import Image

field_type=None

def show_header():
    path = os.path.dirname(__file__)
    logo = Image.open(path + "\\" + 'page_header.png')
    st.image(logo, caption='', use_container_width=True)

def extend_list(list1, list2):

    list1.extend(list2)

    return list1;

def get_idx(dlist, value):

    return dlist.index(value);

def get_dict_files(dict_type):

    dict_files = []

    for dict_f in glob.glob("*.dict"):
        df = pd.read_csv(dict_f, index_col=0)
        if df.loc['Dict Type', 'Parameter']==dict_type:
            dict_files.append(dict_f)

    return dict_files;


def get_file_list(extensions, include_none=True):
    '''

    :param extensions:
    :param include_none:
    :return:
    '''
    if include_none:
        file_list = ['--None--']
    else:
        file_list = []

    for ext in extensions:
        file_list = extend_list(file_list, glob.glob("*" + ext))

    return file_list;

def load_file(infile):
    '''

    :param infile:
    :return:
    '''
    if ".dm" in infile:
        df = pyrpa.io.read_datamine(infile)
    elif ".csv" in infile:
        df = pd.read_csv(infile)
    else:
        raise ValueError("Invalid file type")
    return df;

def upload_or_select(extensions, display_text="Data File (.csv or .dm)", key="file", sidebar=True, initial_value=None):
    """Show a drag-and-drop file uploader then a directory-scan selectbox as fallback.
    Upload takes priority. Returns (filename_str, DataFrame) or (None, None)."""
    widget = st.sidebar if sidebar else st

    uploaded = widget.file_uploader(
        display_text,
        type=[e.lstrip('.') for e in extensions],
        key=key + "_upload",
    )
    if uploaded is not None:
        name = uploaded.name
        if '.dm' in name:
            import tempfile
            tmp_path = os.path.join(tempfile.gettempdir(), name)
            with open(tmp_path, 'wb') as f:
                f.write(uploaded.getvalue())
            df = pyrpa.io.read_datamine(tmp_path)
        else:
            df = pd.read_csv(uploaded)
        return name, df

    infiles = get_file_list(extensions)
    if initial_value is not None and initial_value in infiles:
        idx = infiles.index(initial_value)
    else:
        idx = 0
    infile = widget.selectbox("...or select from folder", infiles, index=idx, key=key + "_select")
    if infile != "--None--":
        return infile, load_file(infile)
    return None, None

def get_header(df):
    '''

    :param df:
    :return:
    '''

    return extend_list(['--None--'],df.columns)


def define_sample(df, gradefields, holeid, xyzfields, domainf, weightf):

    '''

    :param df:
    :param gradefields:
    :param holeid:
    :param xyzfields:
    :param domainf:
    :param weightf:
    :return:
    '''

    assert gradefields != "--None--", "Select a grade field"
    assert holeid != "--None--", "Select grade field"
    assert len(xyzfields) == 3, "Select 3 coordinate fields"

    if domainf == "--None--":
        domainf = None
    if weightf == "--None--":
        weightf = None

    smp_obj = pyrpa.smp.Sample(data=df, gradefields=gradefields,
                               holeid=holeid, xyzfields=xyzfields,
                               domainf=domainf, weightf=weightf)
    return smp_obj;

def invalid_number_handling(df, gradefields, option):
    df_out = df.copy()
    for gf in gradefields:
        if option == 'Ignore':
            try:
                df_out = df_out[df_out[gf].str.isnumeric].copy()
            except:
                pass
        else:
            try:
                df_out[gf] = df_out[gf].fillna(0.)
                df_out.loc[df_out[gf].str.isalnum, [gf]] = 0.
            except:
                pass
    return df_out;

def guess_field(header, type=None):

    comb_dict = {"xyzfields": [['X', 'Y', 'Z'],
                             ['midx', 'midy', 'midz'],
                             ['EAST', 'NORTH', 'ELEV'],
                             ['mid_x', 'mid_y', 'mid_z'],
                             ['XPT', 'YPT', 'ZPT'],
                             ['Easting', 'Norting', 'Elevation'],
                             ['LOCATIONX', 'LOCATIONY', 'LOCATIONZ']],
                 "holeid": ['BHID', 'HOLEID', 'holeid'],
                 "weightf": ['length', 'LENGTH', 'dcweight'],
                 "domainf": ['ZONE', 'DOMAIN', 'ROCK', 'rock', 'bound']
                 }

    combinations  = comb_dict[type]
    found = 0
    for comb in combinations:
        if found == 0:
            if isinstance(comb, list):
                if all(x in header for x in comb):
                    fields = comb
                    found = 1
            else:
                if comb in header:
                    fields = comb
                    found = 1
    if found == 0:
        fields = None

    return fields;

def selectbox(selection, options, display_text, key, guessheader=False, field_type=None):

    if guessheader and field_type is not None:
        selection = guess_field(header=options, type=field_type)

    if selection != '--None--':
        idx = get_idx(options, selection)
    else:
        idx = 0

    return st.sidebar.selectbox(display_text, options=options, index=idx, key=key);

def multiselect(options, display_text, default_list, default_dictval, key, guessheader=False, field_type='xyzfields'):
    
    if default_list != [""] and default_list != []:
        if isinstance(default_list, float):
            default_list = []
        else:
            default_list = strip_dflist(default_dictval)

    else:
        if guessheader:
            default_list = guess_field(options, field_type)
        else:
            default_list = []

    default_list = st.sidebar.multiselect(display_text, options=options, default=default_list, key=key)

    for i, c in enumerate(default_list):
        if i == 0:
            default_dictval = str(c)
        else:
            default_dictval += ("," + str(c))

    return default_list, default_dictval;


def radio(selection, options, display_text, key, sidebar=False):

    if selection != '--None--':
        idx = get_idx(options, selection)
    else:
        idx = 0
    if sidebar:
        return st.sidebar.radio(display_text, options=options, index=idx, key=key);
    else:
        return st.radio(display_text, options=options, index=idx, key=key);

def strip_dflist(dflist):
    '''
    Function to convert a list stored as a text string back to a list
    :param dflist: str
        list stored as text string
    :return: list
        list string converted back to a list
    '''
    stripped_list = dflist.strip("][").split(',')
    if len(stripped_list) == 1:
        stripped_list =  stripped_list[0].split(',')
    for i in range(len(stripped_list)):
        stripped_list[i] = stripped_list[i].strip("'")
        stripped_list[i] = stripped_list[i].strip('"')
    return stripped_list;

def update_keys(_temp_dict, dict_type='Capping'):

    ignore_values = ["Dict Type", "Description", "Filename"]

    for key in _temp_dict.index.values:
        if key not in ignore_values:
            _temp_dict.loc[key, 'Parameter'] = st.get_option(key=key)
            _temp_dict.to_csv('temp_' + dict_type + "_dict")
            _temp_dict = pd.read_csv('temp_' + dict_type + "_dict", index_col=0)
            st.set_option(key=key, value=_temp_dict.loc[key, 'Parameter'])

def make_whitespace(number_of_lines=1):

    for i in range(number_of_lines):
        st.markdown("")










