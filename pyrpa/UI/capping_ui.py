# import sys
# from importlib import reload
# import streamlit as st
# from pyrpa.UI import common
# import pandas as pd
# import matplotlib.pyplot as plt
# import pyrpa.capping
# import numpy as np
# import plotly.graph_objects as go
# import plotly.express as px
# from PIL import Image
# import os
#
# if sys.version_info[0] < 3:
#     reload(sys)
#     sys.setdefaultencoding("utf-8")
#
# @st.cache
# def do_nothing():
#     pass
#
# index = ["Dict Type", "Filename", "Grade Field", "XYZ Fields", "Domain Field", "Domains",
#          "Weight Field", "Invalid Numbers", "Cap Granularity",
#          "XYZ Plane", "P1", "P2",
#          "CDF Capping Grade",
#          "Histogram Binwidth", "Histogram X Max", "Histogram Y Max", "Histogram Cap", "Histogram Logscale",
#          "Decile Min Cap", "Decile Max Cap", "Disintegration X Min", "Disintegration X Max",
#          "Disintegration Logscale",
#          "Settings File"]
#
# # intialization of the variables
# hide_widgets=False
# infile = None
# df = None
# gradefield = None
# xyzfields = []
# domainf = None
# domains = []
# weightf = None
# inv_num = None
# cap_granularity = None
# lp_cap = None
# plane = None
# p1=None
# p2=None
# hist_binwidth = None
# hist_xmax = None
# hist_ymax = None
# hist_cap=None
# hist_log=False
# dec_mincap = None
# dec_maxcap = None
# disint_xmin = None
# disint_xmax = None
# disint_log = False
# str_cap = None
# out_settings = ""
#
#
# path = os.path.dirname(__file__)
# logo = Image.open(path + "\\" + 'page_header.png')
# st.image(logo, caption='', use_column_width=True)
# st.title("Capping Analysis")
# st.info("For positively skewed grade distributions, a small number of extreme values can have a disproportionate impact "
#         "on the resulting resource estimate. The management of these values is critical to producing resource estimates "
#         "that are a reasonable representation of the the grade and tonnes that will achieved if the deposit were to be "
#         "mined.")
# '''
# The capping of grades is the most widely accepted technique for managing extreme values in the distribution. When
# deciding on an appropriate capping level, the objective, or process is as follows:
# * The most important step is reviewing the geological domain and the spatial location of the extreme values.
# * Review the statistical populations by means of log probability plots, histograms and disintegration analysis
# * Try and understand what the high grades represent in terms of risk in the population (decile analysis)
# * Asses the probability of extreme values within the mine plan
# '''
# st.sidebar.markdown("## Parameters")
#
# if st.sidebar.checkbox("Load Settings"):
#     settings_files = common.get_dict_files("Capping")
#     settings_file = st.sidebar.selectbox("Capping Settings File", settings_files)
#     settings_df = pd.read_csv(settings_file, index_col=0)
#
#     # fill settings variables
#     infile = settings_df.loc['Filename', 'Parameter']
#
#     df = common.load_file(infile)
#
#     gradefield = settings_df.loc['Grade Field', 'Parameter']
#     xyzfields = settings_df.loc['XYZ Fields', 'Parameter'].strip("][").split(', ')
#     for i in range(len(xyzfields)):
#         xyzfields[i] = xyzfields[i].strip("'")
#     domainf = settings_df.loc['Domain Field', 'Parameter']
#     domains = settings_df.loc['Domains', 'Parameter'].strip("][").split(', ')
#
#     if domainf != "None" and domainf != "--None--":
#         dt = df[domainf].dtype
#         for i in range(len(domains)):
#             if "'" in domains[i]:
#                 domains[i] = domains[i].strip("'")
#
#     weightf = settings_df.loc['Weight Field', 'Parameter']
#     inv_num = settings_df.loc['Invalid Numbers', 'Parameter']
#     cap_granularity = settings_df.loc["Cap Granularity", 'Parameter']
#     plane = settings_df.loc["XYZ Plane", 'Parameter']
#     p1 = float(settings_df.loc["P1", 'Parameter'])
#     p2 = float(settings_df.loc["P2", 'Parameter'])
#     lp_cap = float(settings_df.loc["CDF Capping Grade", 'Parameter'])
#     hist_binwidth = float(settings_df.loc["Histogram Binwidth", 'Parameter'])
#     hist_xmax = float(settings_df.loc["Histogram X Max", 'Parameter'])
#     hist_ymax = int(settings_df.loc["Histogram Y Max", 'Parameter'])
#     hist_cap = float(settings_df.loc["Histogram Cap", 'Parameter'])
#     hist_log = settings_df.loc["Histogram Logscale", 'Parameter']
#     if hist_log == "False":
#         hist_log = False
#     else:
#         hist_log = True
#     dec_mincap =float(settings_df.loc["Decile Min Cap", 'Parameter'])
#     dec_maxcap = float(settings_df.loc["Decile Max Cap", 'Parameter'])
#     disint_xmin = float(settings_df.loc["Disintegration X Min", 'Parameter'])
#     disint_xmax = float(settings_df.loc["Disintegration X Max", 'Parameter'])
#     disint_log = settings_df.loc["Disintegration Logscale", 'Parameter']
#     out_settings = settings_df.loc['Settings File', 'Parameter']
#
# infiles = common.get_file_list([".csv", ".dm"])
#
# if infile is not None:
#     idx = common.get_idx(infiles, infile)
# else:
#     idx = 0
#
# infile = st.sidebar.selectbox("Data File (.csv or .dm)", infiles, index=idx)
#
# if infile != "--None--":
#
#     if df is None:
#         df = common.load_file(infile)
#     header = common.get_header(df)
#
#     if gradefield is not None:
#         idx = common.get_idx(header, gradefield)
#     else:
#         idx = 0
#
#     gradefield = st.sidebar.selectbox("Grade Field", header, index=idx)
#
#     if xyzfields == []:
#         common.gu
#         xyzfields = common.guess_field(header, field_type='xyzfields')
#         if xyzfields is None:
#             xyzfields = []
#
#     xyzfields = st.sidebar.multiselect("XYZ Fields", header, xyzfields)
#
#     if domainf is not None:
#         idx = common.get_idx(header, domainf)
#     else:
#         domainf = common.guess_field(header, 'domainf')
#         if domainf is not None:
#             idx = common.get_idx(header, domainf)
#         else:
#             idx = 0
#
#     domainf = st.sidebar.selectbox("Domain Field", header, index=idx)
#
#     if domainf != "--None--":
#         domain_options = df[domainf].unique()
#         domain_options = [str(i) for i in domain_options]
#
#         domains = st.sidebar.multiselect("Select Domains", domain_options, domains)
#         if len(domains)>0:
#             df_filt = df[df[domainf].isin(domains)].copy()
#         else:
#             df_filt = df.copy()
#     else:
#         df_filt = df.copy()
#
#     if weightf is not None:
#         idx = common.get_idx(header, weightf)
#     else:
#         weightf = common.guess_field(header, 'weightf')
#         if weightf is not None:
#             idx = common.get_idx(header, weightf)
#         else:
#             idx = 0
#
#     weightf = st.sidebar.selectbox("Weight Field", header, index=idx)
#
#     if cap_granularity is None:
#         cap_granularity = 5.
#
#     cap_granularity = st.sidebar.text_input("Set Capping Granularity", value=cap_granularity)
#     cap_granularity = float(cap_granularity)
#
#     if gradefield != "--None--" and len(xyzfields)==3:
#
#         if st.sidebar.checkbox("Hide Widgets"):
#             hide_widgets=True
#
#         if inv_num is not None:
#             idx = common.get_idx(['Ignore', 'Replace with Zero'], inv_num)
#         else:
#             idx = 0
#
#         inv_num = st.sidebar.radio("Invalid Number Handling", ['Ignore', 'Replace with Zero'], index=idx)
#         df_valid = common.invalid_number_handling(df_filt, gradefield, inv_num)
#         smp_obj = common.define_sample(df=df_valid, gradefields=[gradefield], holeid="",
#                                        xyzfields=xyzfields, domainf=domainf, weightf=weightf)
#         pd.set_option('precision', 2)
#
#         #------------------------------------------------------------------------------------------------------#
#
#         cap_obj = pyrpa.capping(samples=smp_obj, gradefield=gradefield)
#
#         #------------------------------------------------------------------------------------------------------#
#         # Location map
#
#         st.markdown("## Location of Extreme Values")
#         st.info("Plan, section and 3D views of the locations of extreme values are important for making decisions with "
#                 "respect to the capping level selected. For example, extreme values clustered together represent less "
#                 "risk in the area where they are located than an extreme value surrounded by low grades. In many cases "
#                 "a two tier management is required; 1. To restrict the disproportionate amount of metal associated "
#                 "with the high grade, and 2. To restrict the extrapolation of the high grades in sparsely sampled areas "
#                 "or areas where isolated high grades are surrounded by low grades.")
#
#
#         if plane is not None:
#             idx = common.get_idx(['XY', 'XZ', 'YZ'], plane)
#         else:
#             idx=0
#
#         if p1 is None:
#             p1 = 95.
#         if p2 is None:
#             p2 = 99.
#
#         if not hide_widgets:
#
#             plane = st.radio("Location Map Plane", ['XY', 'XZ', 'YZ'], index=idx)
#             p1 = st.slider("P1", 50., 100., p1, 0.1, key='p1slider')
#             p2 = st.slider("P2", 90., 100., p2, 0.1, key='p21slider')
#
#         cap_obj.location_map(plane=plane, p1=p1/100., p2=p2/100.)
#
#         st.pyplot()
#
#         # ------------------------------------------------------------------------------------------------------#
#         # Alternative Location Mape
#         pp=(smp_obj.data[gradefield].min(), smp_obj.data[gradefield].max())
#         if not hide_widgets:
#             pp = st.slider("", smp_obj.data[gradefield].min(), smp_obj.data[gradefield].max(),
#                         pp, cap_granularity, key='pp2slider')
#
#         pp1 = pp[0]
#         pp2 = pp[1]
#
#         filt1 = smp_obj.data[gradefield] >= pp1
#
#         filt2 = smp_obj.data[gradefield] >= pp2
#
#         fig = go.Figure(data=[go.Scatter3d(
#             x=smp_obj.data[xyzfields[0]],
#             y=smp_obj.data[xyzfields[1]],
#             z=smp_obj.data[xyzfields[2]],
#             mode='markers',
#             marker=dict(
#                 size=1,
#                 color='black',  # set color to an array/list of desired values
#                 colorscale='Viridis',  # choose a colorscale
#                 opacity=0.8), name="All Data"),
#             go.Scatter3d(
#                 x=smp_obj.data[xyzfields[0]][filt1],
#                 y=smp_obj.data[xyzfields[1]][filt1],
#                 z=smp_obj.data[xyzfields[2]][filt1],
#                 mode='markers',
#                 marker=dict(
#                     size=6,
#                     color='green',  # set color to an array/list of desired values
#                     colorscale='Viridis',  # choose a colorscale
#                     opacity=0.8), name=">=" + str(np.round(pp1, 0))),
#             go.Scatter3d(
#                 x=smp_obj.data[xyzfields[0]][filt2],
#                 y=smp_obj.data[xyzfields[1]][filt2],
#                 z=smp_obj.data[xyzfields[2]][filt2],
#                 mode='markers',
#                 marker=dict(
#                     size=8,
#                     color='red',  # set color to an array/list of desired values
#                     colorscale='Viridis',  # choose a colorscale
#                     opacity=0.8), name=">=" + str(np.round(pp2, 0)))
#         ])
#
#         # tight layout
#         fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))
#         fig.update_layout(scene_aspectmode='data')
#         st.plotly_chart(fig)
#
#         # ------------------------------------------------------------------------------------------------------#
#         # Log Probability Plot
#         st.markdown("## Log Probability Plot")
#         st.info("The log probability plot is useful for identifying thresholds within the sample population at "
#                 "which values become erratic. The plot is scaled by the log of the values on the x-axis and the "
#                 "gaussian frequency (normal score) on the y-axis.  Given these scales, if the sample population were "
#                 "perfectly log normal, the values would plot a straight line. The premise for picking a capping value "
#                 "on the chart is looking for areas where the population deviates from a straight line.  The deviation "
#                 "that should be sought is generally a flattening of the curve as it is at this point that the high "
#                 "grades increase disproportionately as compared to a lognormal distribution.")
#
#         if lp_cap is None:
#             lp_cap = smp_obj.data[gradefield].max()
#
#         if lp_cap > smp_obj.data[gradefield].max():
#             lp_cap = smp_obj.data[gradefield].max()
#
#         if not hide_widgets:
#             lp_cap = st.slider("Log Probability Capping Level", smp_obj.data[gradefield].min(),
#                            smp_obj.data[gradefield].max(),
#                            lp_cap, cap_granularity, key='lpcapslider')
#
#         cap_obj.capping_levels = [lp_cap]
#
#         cap_obj.log_probability_plot(show_caps=True)
#         st.pyplot()
#
#         # ------------------------------------------------------------------------------------------------------#
#         # Histogram
#         st.markdown("## Histogram")
#
#         if hist_binwidth is None:
#             hist_binwidth = 5.
#         if not hide_widgets:
#             hist_binwidth = st.text_input("Bin Width", value=hist_binwidth)
#         hist_binwidth = float(hist_binwidth)
#
#         if hist_xmax is None or hist_xmax > smp_obj.data[gradefield].max():
#             hist_xmax = smp_obj.data[gradefield].max()
#
#         if not hide_widgets:
#             hist_xmax = st.slider("X-Axis maximum", smp_obj.data[gradefield].min(),
#                                smp_obj.data[gradefield].max(),
#                                hist_xmax, cap_granularity, key='histxmaxslider')
#
#         if hist_ymax is None:
#             hist_ymax = len(smp_obj.data)
#
#         if not hide_widgets:
#             hist_ymax = st.slider("Y-Axis maximum", 0,
#                                len(smp_obj.data),
#                                hist_ymax, key='histymax')
#
#         if not hide_widgets:
#             hist_log = st.checkbox("Log Histogram", value=hist_log)
#
#         cap_obj.histogram(bin_width=hist_binwidth, xmax=hist_xmax, ymax=hist_ymax, log=hist_log)
#
#         if hist_cap is None or hist_cap > hist_xmax:
#             hist_cap = hist_xmax
#
#         if not hide_widgets:
#             hist_cap = st.slider("Histogram Capping Level", smp_obj.data[gradefield].min(),
#                                hist_xmax,
#                                hist_cap, cap_granularity, key='histcapslider')
#
#         plt.plot([hist_cap, hist_cap], [0., len(cap_obj.samples.data)], '--g')
#         plt.legend(['Capping Level Selected', 'Histogram'], loc='best')
#         st.pyplot()
#
#         # ------------------------------------------------------------------------------------------------------#
#         # Decile Analysis
#
#         st.markdown("## Decile Analysis")
#
#         if dec_mincap is None:
#             dec_mincap = ""
#         if dec_maxcap is None:
#             dec_maxcap = ""
#
#         if not hide_widgets:
#             dec_mincap = st.text_input("Minimum cap to check", dec_mincap)
#             dec_maxcap = st.text_input("Maximum cap to check", dec_maxcap)
#
#         if dec_mincap != '' and dec_maxcap != '' and float(dec_maxcap) > float(dec_mincap):
#
#             dec_mincap = float(dec_mincap)
#             dec_maxcap = float(dec_maxcap)
#
#             cap_obj.capping_levels = np.arange(dec_mincap, dec_maxcap + cap_granularity, cap_granularity)
#             dec_df = cap_obj.decile_analysis(plot=True)
#             st.pyplot()
#
#             if not hide_widgets:
#                 if st.checkbox("Show Table"):
#                     st.dataframe(dec_df)
#
#         # ------------------------------------------------------------------------------------------------------#
#         # Disintegration Analysis
#         st.markdown("## Disintegration Analysis")
#
#         if disint_xmin is None or disint_xmin > smp_obj.data[gradefield].max():
#             disint_xmin = smp_obj.data[gradefield].min()
#
#         if disint_xmax is None or disint_xmax > smp_obj.data[gradefield].max():
#             disint_xmax = smp_obj.data[gradefield].max()
#
#         if not hide_widgets:
#
#             disint_xmin = st.slider("X-Axis minimum", smp_obj.data[gradefield].min(),
#                                smp_obj.data[gradefield].max(),
#                                disint_xmin, cap_granularity, key='disintxminslider')
#
#             disint_xmax = st.slider("X-Axis maximum", smp_obj.data[gradefield].min(),
#                                     smp_obj.data[gradefield].max(),
#                                     disint_xmax, cap_granularity, key='disintxmaxslider')
#
#             disint_log = st.checkbox("Log Scale X", value=disint_log)
#
#         disint_df = cap_obj.disintegration_analysis(plot=True, logx=disint_log, xmin=disint_xmin, xmax=disint_xmax)
#         st.pyplot()
#
#         # ------------------------------------------------------------------------------------------------------#
#         # Stripe Plot
#
#         st.markdown("## Strip Plot")
#
#         str_df = smp_obj.data.copy()
#
#         if str_cap is None:
#             str_cap = str_df[gradefield].max()
#
#         if not hide_widgets:
#
#             str_cap = st.slider("Strip Plot Capping Level", str_df[gradefield].min(),
#                                str_df[gradefield].max(),
#                                str_cap, cap_granularity, key='strcapslider')
#
#         str_df['x']=gradefield
#         str_df['color'] = 'Capped'
#         str_df.loc[str_df[gradefield]>=str_cap, 'color'] = 'Uncapped'
#         str_fig = px.strip(str_df, x='x', y=gradefield, orientation="v", color="color", stripmode='overlay')
#         st.plotly_chart(str_fig)
#
#
#         # ------------------------------------------------------------------------------------------------------#
#         # Cutting Curve
#
#
#         # ------------------------------------------------------------------------------------------------------#
#         # Capping Matrix
#         # ------------------------------------------------------------------------------------------------------#
#
#         st.markdown("## Capping Comparison")
#         method = ['Log Probability', 'Histogram', 'Decile Analysis', 'Disintegration Analysis', 'Strip Plot']
#         caps = [lp_cap, hist_cap, -99, -99, str_cap]
#         cap_matrix = pd.DataFrame({"Method": method, "Capping Observation": caps}, index=None)
#         st.table(cap_matrix)
#
#         # ------------------------------------------------------------------------------------------------------#
#         # save settings
#
#
#         out_settings = st.sidebar.text_input("Save Settings File", value=out_settings)
#
#         if out_settings != "":
#             if ".dict" not in out_settings:
#                 out_settings += ".dict"
#             if st.sidebar.button("Save", key="save1"):
#                 settings = ['Capping', infile, gradefield, xyzfields, domainf, domains, weightf, inv_num, cap_granularity,
#                             plane, p1, p2,
#                             lp_cap,
#                             hist_binwidth, hist_xmax, hist_ymax, hist_cap, hist_log,
#                             dec_mincap, dec_maxcap,
#                             disint_xmin, disint_xmax, disint_log,
#                             out_settings]
#                 pd.DataFrame({'Parameter': settings}, index=index).to_csv(out_settings)
# 
#
#
#
#
