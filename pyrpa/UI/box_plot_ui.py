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
gradefield='--None--'
domainfield='--None--'
subdomainfield='--None--'

infile, df = common.upload_or_select([".csv", ".dm"])

if df is not None:

    header = common.get_header(df)

    gradefield = common.selectbox(selection=gradefield, options=header, display_text="Grade Field", key='Grade Field')
    domainfield = common.selectbox(selection=domainfield, options=header, display_text="Domain Field", key='Domain Field')
    subdomainfield = common.selectbox(selection=subdomainfield, options=header, display_text="Subdomain Field", key='Subdomain Field')
    logy = st.sidebar.checkbox("Log", key='logy')

    common.show_header()
    st.info('## Box Plot')

    if gradefield != '--None--':

        if subdomainfield == '--None--':
            df['color']='_'
            for i, dom in enumerate(df[domainfield].unique()):
                df['color'][df[domainfield]==dom] = px.colors.DEFAULT_PLOTLY_COLORS[i]

            fig = px.box(data_frame=df, x=domainfield, y=gradefield, points=False, color='color')
            fig.update_layout(yaxis_type="log")

        else:

            df = df.sort_values(by=[domainfield, subdomainfield])

            fig = go.Figure()

            for i, dom in enumerate(df[domainfield].unique()):

                x = df[subdomainfield][df[domainfield]==dom]

                fig.add_trace(go.Box(
                    y=df[gradefield][df[domainfield]==dom],
                    x=x,
                    name=str(dom), boxpoints=False))

            fig.update_layout(yaxis_title=gradefield, boxmode='group')
            fig.update_layout(yaxis_type="log", width=900, height=600)

        st.plotly_chart(fig)

