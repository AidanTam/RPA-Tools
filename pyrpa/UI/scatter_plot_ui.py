import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pyrpa.UI.common as common
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype


infile=None
df=None
variable1=None
variable2=None
colourfield=None
pointsize=4

infile, df = common.upload_or_select([".csv", ".dm"])

if df is not None:
    header = common.get_header(df)

    if variable1 is not None:
        idx = common.get_idx(header, variable1)
    else:
        idx = 0

    variable1 = st.sidebar.selectbox("Variable 1", header, index=idx)
    logx = st.sidebar.checkbox("Log", key='log1')
    marg_x = st.sidebar.selectbox('Marginal X Axis', ['--None--', 'histogram', 'box', 'violin'])
    if variable2 is not None:
        idx = common.get_idx(header, variable2)
    else:
        idx = 0

    variable2 = st.sidebar.selectbox("Variable 2", header, index=idx)
    logy = st.sidebar.checkbox("Log", key='log2')
    marg_y = st.sidebar.selectbox('Marginal Y Axis', ['--None--', 'histogram', 'box', 'violin'])



    if colourfield is not None:
        idx = common.get_idx(header, colourfield)
    else:
        idx = 0

    colourfield = st.sidebar.selectbox("Colour points by:", header, index=idx)


    if st.sidebar.checkbox("Size Values by Numeric Value"):

        if not isinstance(pointsize, int):
            idx = common.get_idx(header, pointsize)
        else:
            idx = 0
        pointsize = st.sidebar.selectbox("Point Size Field", header, index=idx)


    else:
        pointsize = st.sidebar.number_input('Point Size', value=4)

    if variable1 != "--None--" and variable2 != "--None--":

        hoverbox = []
        hoverbox.append(variable1)
        hoverbox.append(variable2)

        if colourfield is not None and colourfield != "--None--":
            hoverbox.append(colourfield)

        if not isinstance(pointsize, int) and pointsize != '--None--':
            size = pointsize
        else:
            size = None

        if size != None:
            hoverbox.append(size)

        if marg_x == '--None--':
            marginal_x=None
        else:
            marginal_x=marg_x

        if marg_y == '--None--':
            marginal_y=None
        else:
            marginal_y=marg_y

        hoverbox = st.multiselect(label='Hover Text to Show', options=header, default=hoverbox, key='hover')

        if colourfield == '--None--':
            fig = px.scatter(df, x=variable1, y=variable2, marginal_x=marginal_x, marginal_y=marginal_y,
                             size=size, hover_data=hoverbox)
        elif not is_numeric_dtype(df[colourfield]):
            fig = px.scatter(df, x=variable1, y=variable2, marginal_x=marginal_x, marginal_y=marginal_y,
                             color=colourfield, size=size, hover_data=hoverbox)
        else:
            colourscale = st.sidebar.selectbox("Select Colour Scale:", ['Blackbody',
                                                                        'Bluered',
                                                                        'Blues',
                                                                        'Earth',
                                                                        'Electric',
                                                                        'Greens',
                                                                        'Greys',
                                                                        'Hot',
                                                                        'Jet',
                                                                        'Picnic',
                                                                        'Portland',
                                                                        'Rainbow',
                                                                        'RdBu',
                                                                        'Reds',
                                                                        'Viridis',
                                                                        'YlGnBu',
                                                                        'YlOrRd'], index=11)

            fig = px.scatter(df, x=variable1, y=variable2, color=colourfield,
                             color_continuous_scale=colourscale, size=size, hover_data=hoverbox)
        if logx:
            fig.update_layout(xaxis_type="log")
        if logy:
            fig.update_layout(yaxis_type="log")



        st.plotly_chart(fig)
