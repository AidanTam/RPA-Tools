import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import pyrpa.UI.common as common
import random

df_colors = ['aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige',
             'bisque', 'black', 'blanchedalmond', 'blue', 'blueviolet', 'brown',
             'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'coral', 'cornflowerblue',
             'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray',
             'darkgrey', 'darkgreen', 'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange',
             'darkorchid', 'darkred', 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray',
             'darkslategrey', 'darkturquoise', 'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dimgrey',
             'dodgerblue', 'firebrick', 'floralwhite', 'forestgreen', 'fuchsia', 'gainsboro', 'ghostwhite', 'gold',
             'goldenrod', 'gray', 'grey', 'green', 'greenyellow', 'honeydew', 'hotpink', 'indianred', 'indigo', 'ivory',
             'khaki', 'lavender', 'lavenderblush', 'lawngreen', 'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan',
             'lightgoldenrodyellow', 'lightgray', 'lightgrey', 'lightgreen', 'lightpink', 'lightsalmon', 'lightseagreen',
             'lightskyblue', 'lightslategray', 'lightslategrey', 'lightsteelblue', 'lightyellow', 'lime', 'limegreen', 'linen',
             'magenta', 'maroon', 'mediumaquamarine', 'mediumblue', 'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue',
             'mediumspringgreen', 'mediumturquoise', 'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'navajowhite',
             'navy', 'oldlace', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred',
             'papayawhip', 'peachpuff', 'peru', 'pink', 'plum', 'powderblue', 'purple', 'red', 'rosybrown', 'royalblue', 'rebeccapurple', 'saddlebrown',
             'salmon', 'sandybrown', 'seagreen', 'seashell', 'sienna', 'silver', 'skyblue', 'slateblue', 'slategray', 'slategrey', 'snow',
             'springgreen', 'steelblue', 'tan', 'teal', 'thistle', 'tomato', 'turquoise', 'violet', 'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen']

infile=None
df=None
width=None
height=None
labels=None

infile, df = common.upload_or_select([".csv", ".dm"])

if df is not None:
    header = common.get_header(df)

    if width is not None:
        idx = common.get_idx(header, width)
    else:
        idx = 0

    width = st.sidebar.selectbox("Width", header, index=idx)

    if height is not None:
        idx = common.get_idx(header, height)
    else:
        idx = 0

    height = st.sidebar.selectbox("height", header, index=idx)

    if labels is not None:
        idx = common.get_idx(header, labels)
    else:
        idx = 0

    labels = st.sidebar.selectbox("Labels", header, index=idx)

    if width != "--None--" and height != "--None--" and labels != '--None--':
        
        if st.sidebar.checkbox("Sorted by Height"):
            df = df.sort_values(by=[height])
        
        df['cumwidth'] = df[width].cumsum()
        df['center'] = df['cumwidth'] - df[width] / 2.

        fig = go.Figure(data=[go.Bar(
            x=df.center,
            y=df[height],
            width=df[width],
            marker_color=random.choices(df_colors, k=len(df))
        )])
        fig.update_layout(xaxis = dict(
        tickmode = 'array',
        tickvals = df.center,
        ticktext = df[labels],
        tickangle=90))
        fig.update_layout(
            title="Variable Width Bar Chart",
            xaxis_title=width,
            yaxis_title=height,
            autosize=False,
            width=100,
            height=100,
            paper_bgcolor="white",
        )

        st.plotly_chart(fig)




