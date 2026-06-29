import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import pyrpa.UI.common as common
import pyrpa
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

st.title("Gammabar Plot")
st.info("This function is GSLIB gammabar implementation. Rotations are the GSLIB conventions. "
        "If the variogram is not standardised it will standardised internally to produce a gammabar value between"
        " 0 and 1")

st.sidebar.markdown("## Block Size")
minb = st.sidebar.text_input("Mininum block size to test",value='5.')
maxb = st.sidebar.text_input("Maximum block size", value='10.')
stepb = st.sidebar.text_input("Step Size", value='5.')
bsizes = np.arange(float(minb), float(maxb) + float(stepb), float(stepb))
st.sidebar.markdown("## Discretization")
xd=st.sidebar.number_input("X", value=5, key="disc_x")
yd=st.sidebar.number_input("Y", value=5, key="disc_y")
zd=st.sidebar.number_input("Z", value=5, key="disc_z")
disc = [xd, yd, zd]
st.sidebar.markdown("## Variogram")
st.sidebar.markdown("### Rotation")
xrt=st.sidebar.number_input("Z", value=0., key="rot_z")
yrt=st.sidebar.number_input("X", value=0., key="rot_x")
zrt=st.sidebar.number_input("Y", value=0., key="rot_y")
rot = [xrt, yrt, zrt]
nugget = st.sidebar.number_input("Nugget", value=0.1)
ns = st.sidebar.number_input("Number of Structures", value=1)
struct_types = []
variances = []
vranges = []
st.sidebar.markdown("### Structure Types")
for i in range(ns):
    stype = st.sidebar.selectbox("Structure Type" + str(i+1), options=[1,2], key="s" + str(i+1))
    struct_types.append(stype)
st.sidebar.markdown("### Variances")
for i in range(ns):
    s = st.sidebar.number_input("C" + str(i+1), value=0.1, key="c" + str(i+1))
    variances.append(s)
variances = np.array(variances)
sumvar = sum(variances) + nugget
nugget /= sumvar
variances /= sumvar
st.sidebar.markdown("### Ranges")
for i in range(ns):
    xr = st.sidebar.number_input("X Range Structure " + str(i+1), value=100, key="xr" + str(i+1))
    yr = st.sidebar.number_input("Y Range Structure " + str(i + 1), value=100, key="yr" + str(i + 1))
    zr = st.sidebar.number_input("Z Range Structure " + str(i + 1), value=100, key="zr" + str(i + 1))
    vranges.append([xr,yr,zr])

results = []

for i in bsizes:
    for j in bsizes:
        for k in bsizes:
            blocksize = [i,j,k]
            btext = str(i) + " X " + str(j)+ " X " + str(k)

            gammabar = pyrpa.gcos.gammabar(block_size=blocksize,
                                           discretisation=disc,
                                           rotation=rot,
                                           nugget=nugget,
                                           structure_types=struct_types,
                                           variances=variances,
                                           vranges=vranges)

            results.append([btext, float(gammabar), i, j, k])
df = pd.DataFrame(data=results, columns=["Block Size", "Gammabar", "XINC", 'YINC', 'ZINC'])
if st.checkbox("Show Table"):
    st.table(df)

gp_plot = st.selectbox("Group Plot By", options=['XINC', 'YINC', 'ZINC'])
sp_plot = st.selectbox("Size Points By", options=['XINC', 'YINC', 'ZINC'])

df[gp_plot + "_str"] = df[gp_plot].apply(lambda x:str(x))

fig = px.scatter(df, x='Block Size', y='Gammabar',
                             color=gp_plot + "_str", size=sp_plot)
st.plotly_chart(fig)
outfile = st.text_input("Save as csv", value="")
if st.button("Save") and outfile!="":
    df.to_csv(outfile, index=False)




