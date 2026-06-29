import streamlit as st
import sys
import os
from importlib import reload
import pandas as pd
from pyrpa.UI import common
import pyrpa
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
try:
    from docxtpl import DocxTemplate, InlineImage
    from docx.shared import Mm
except ImportError:
    DocxTemplate = InlineImage = Mm = None
# import openai
import io
import tempfile

# from st_aggrid import AgGrid

try:
    _report_template = os.path.join(os.path.dirname(__file__), 'SLR amazing report.docx')
    doc = DocxTemplate(_report_template) if DocxTemplate and os.path.exists(_report_template) else None
except Exception:
    doc = None
if 'AI_Intorduction' not in st.session_state:
    st.session_state['AI_Intorduction'] = ""
if 'piechartimage' not in st.session_state:
    st.session_state['piechartimage'] = None
fig_list = {}
# context = {'project_name':ProjectName}
          # 'fig1':InlineImage(doc,st.session_state.fig1,width=Mm(160), height=Mm(80)),
          # 'fig2':InlineImage(doc,st.session_state.fig2,width=Mm(160), height=Mm(80)),
          # 'fig3':InlineImage(doc,st.session_state.fig3,width=Mm(160), height=Mm(80))}


st.set_page_config(layout="wide")

if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding("utf-8")

st.sidebar.markdown("## Parameters")

# set an empty temporary dictionary
_temp_dict = None

index = ['Dict Type', 'Description', 'Filename', 'Grade Field', 'XYZ Fields',
         'Domain Field', 'Domains', 'Weight Field', 'Invalid Numbers',
         'Low Cap', 'Selected Cap', 'High Cap',
         'XYZ Plane',
         'Histogram Bin', 'Histogram X Max', 'Histogram Y Max',
         'Settings File']

defaults = ['Capping', "[Project Description]", '--None--', '--None--', '',
            '--None--', '', '--None--', 'Ignore',
            -99., -99., -99.,
            '--None--',
            5., -99., -99.,
            '']

print_layout=False

if _temp_dict is None:
    _temp_dict = pd.DataFrame({'Parameter': defaults}, index=index) # create a df with the "defaults" list
ProjectName = st.sidebar.text_input('Project Name', value='--Project Name--')

if st.sidebar.checkbox("Load Settings"):
    settings_files = common.get_dict_files("Capping")
    settings_file = st.sidebar.selectbox("Capping Settings File", settings_files, key="Capping Settings File")
    settings_df = pd.read_csv(settings_file, index_col=0)
    _temp_dict = settings_df

#

xyzfields = common.strip_dflist(_temp_dict.loc['XYZ Fields', 'Parameter'])
domains = common.strip_dflist(_temp_dict.loc['Domains', 'Parameter'])

_temp_dict.loc['Description', 'Parameter'] = st.sidebar.text_input("Description", _temp_dict.loc['Description', 'Parameter'])
_infile, df = common.upload_or_select([".csv", ".dm"], initial_value=_temp_dict.loc['Filename', 'Parameter'], key='Filename')
if _infile is not None:
    _temp_dict.loc['Filename', 'Parameter'] = _infile

# big outer if is checking to see if filename is defined

if df is not None:
    header = common.get_header(df)

    _temp_dict.loc['Grade Field', 'Parameter'] = common.selectbox(selection=_temp_dict.loc['Grade Field', 'Parameter'],
                                                                       options=header,
                                                                       display_text="Grade Field",
                                                                       key='Grade Field')
    gradeunit = st.sidebar.selectbox('Grade Unit',['g/t','%','ppm','ppb','oz/t','lb/t','kg/t'])
    xyzfields, _temp_dict.loc['XYZ Fields', 'Parameter'] = common.multiselect(options=header,
                                                                              display_text='XYZ Fields',
                                                                              default_list=xyzfields,
                                                                              default_dictval=_temp_dict.loc['XYZ Fields', 'Parameter'],
                                                                              key='XYZ Fields',
                                                                              guessheader=True,
                                                                              field_type='xyzfields')

    _temp_dict.loc['Domain Field', 'Parameter'] = common.selectbox(selection=_temp_dict.loc['Domain Field', 'Parameter'],
                                                                  options=header,
                                                                  display_text="Domain Field",
                                                                  key='Domain Field')

    if _temp_dict.loc['Domain Field', 'Parameter'] != "--None--":

        domain_options = df[_temp_dict.loc['Domain Field', 'Parameter']].unique()
        df[_temp_dict.loc['Domain Field', 'Parameter']] = df[_temp_dict.loc['Domain Field', 'Parameter']].apply(lambda x: str(x))
        domain_options = [str(i) for i in domain_options]

        domains, _temp_dict.loc['Domains', 'Parameter'] = common.multiselect(options=domain_options,
                                                                             display_text='Domains',
                                                                             default_list=domains,
                                                                             default_dictval=_temp_dict.loc['Domains', 'Parameter'],
                                                                             key='Domains',
                                                                             guessheader=False,
                                                                             field_type='domains')

        if len(domains) > 0:
            df_filt = df[df[_temp_dict.loc['Domain Field', 'Parameter']].isin(domains)].copy().reset_index(drop=True)
        else:
            df_filt = df.copy().reset_index(drop=True)
    else:
        df_filt = df.copy().reset_index(drop=True)

    _temp_dict.loc['Weight Field', 'Parameter'] = common.selectbox(selection=_temp_dict.loc['Weight Field', 'Parameter'],
                                                                  options=header,
                                                                  display_text="Weight Field",
                                                                  key='Weight Field')

    if _temp_dict.loc['Weight Field', 'Parameter'] == '--None--':
        weightf = None
    else:
        weightf = _temp_dict.loc['Weight Field', 'Parameter']

    if _temp_dict.loc['Grade Field', 'Parameter'] != "--None--" and len(xyzfields) == 3:

        idx = common.get_idx(['Ignore', 'Replace with Zero'], _temp_dict.loc['Invalid Numbers', 'Parameter']) # idx = index

        _temp_dict.loc['Invalid Numbers', 'Parameter'] = st.sidebar.radio("Invalid Number Handling",
                                                                          ['Ignore', 'Replace with Zero'],
                                                                          index=idx)

        df_valid = common.invalid_number_handling(df_filt, _temp_dict.loc['Grade Field', 'Parameter'],
                                                  _temp_dict.loc['Invalid Numbers', 'Parameter'])

        df_valid = df_valid.sort_values(by=[_temp_dict.loc['Grade Field', 'Parameter']]) # final df after validations and filters

        smp_obj = pyrpa.smp.Sample(data=df_valid,
                                   gradefields=[_temp_dict.loc['Grade Field', 'Parameter']],
                                   holeid=None,
                                   xyzfields=xyzfields,
                                   weightf=weightf)

        # defining the default low, selected, and high cap from the df_valid
        if float(_temp_dict.loc['Low Cap', 'Parameter']) == -99.:
            _temp_dict.loc['Low Cap', 'Parameter'] = round(smp_obj.data[_temp_dict.loc['Grade Field', 'Parameter']].quantile(0.95),2) # smp_obj.data is calling the "df_valid"
        if float(_temp_dict.loc['Selected Cap', 'Parameter']) == -99.:
            _temp_dict.loc['Selected Cap', 'Parameter'] = round(smp_obj.data[_temp_dict.loc['Grade Field', 'Parameter']].quantile(0.975),2)
        if float(_temp_dict.loc['High Cap', 'Parameter']) == -99.:
            _temp_dict.loc['High Cap', 'Parameter'] = round(smp_obj.data[_temp_dict.loc['Grade Field', 'Parameter']].quantile(0.99),2)

        smp_obj.data['Capping Levels'] = 'Uncapped'
        smp_obj.data['Point Size'] = 0.1
        point_sizes = [0.5, 1.0, 1.5]
        smp_obj.data['Point Size3D'] = 1

        for s, i in enumerate(['Low Cap', 'Selected Cap', 'High Cap']):
            # defining capping level
            _temp_dict.loc[i, 'Parameter'] = float(st.sidebar.text_input(i, value=_temp_dict.loc[i, 'Parameter'], key=i))
            filt = smp_obj.data[_temp_dict.loc['Grade Field', 'Parameter']] >= _temp_dict.loc[i, 'Parameter']
            smp_obj.data['Capping Levels'][filt] = i
            smp_obj.data['Point Size'][filt] = point_sizes[s]
            smp_obj.data['Point Size3D'][filt] = float(s + 3)

        # _temp_dict.to_csv('_temp_cap_dict')
        uncapped_color = st.sidebar.color_picker('Uncapped', '#808080')
        lowcap_color = st.sidebar.color_picker('Low Cap', '#0000ff')
        selectedcap_color = st.sidebar.color_picker('Selected Cap', '#008800')
        highcap_color = st.sidebar.color_picker('High Cap', '#ff0000')
        smp_obj.data['Point Size'][smp_obj.data[_temp_dict.loc['Grade Field', 'Parameter']] == smp_obj.data[_temp_dict.loc['Grade Field', 'Parameter']].max()] = 5.

        # save settings stuff ------------------------------------------------------------------------------------------------

        _temp_dict.loc['Settings File', 'Parameter'] = st.sidebar.text_input("Save Capping Settings",
                                                                             value=_temp_dict.loc['Settings File', 'Parameter'],
                                                                             key='Settings File')

        if ".dict" not in _temp_dict.loc['Settings File', 'Parameter'] and _temp_dict.loc['Settings File', 'Parameter'] != ' ':
            _temp_dict.loc['Settings File', 'Parameter'] += ".dict"

        if st.sidebar.button('Save', key='save settings'):
            _temp_dict.to_csv(_temp_dict.loc['Settings File', 'Parameter'])


        if st.sidebar.checkbox("Print layout"):
            print_layout = True
        try:
            _temp_dict2 = pd.read_csv('_temp_cap_dict', index_col=0)
            # revert to previously set settings
            _temp_dict.loc['XYZ Plane', 'Parameter'] = _temp_dict2.loc['XYZ Plane', 'Parameter']
            _temp_dict.loc['Histogram Bin', 'Parameter'] = _temp_dict2.loc['Histogram Bin', 'Parameter']
            _temp_dict.loc['Histogram X Max', 'Parameter'] = _temp_dict2.loc['Histogram X Max', 'Parameter']
            _temp_dict.loc['Histogram Y Max', 'Parameter'] = _temp_dict2.loc['Histogram Y Max', 'Parameter']
        except:
            pass

        common.show_header()
        # with st.expander("Capping Analysis"):
        st.title("Capping Analysis") # main screen

        st.markdown("Description: `" + _temp_dict.loc['Description', 'Parameter'] + "`")
        st.markdown("Filename: `" + _temp_dict.loc['Filename', 'Parameter'] + "`")
        st.markdown("Grade Field: `" + _temp_dict.loc['Grade Field', 'Parameter'] + "`")
        if _temp_dict.loc['Domain Field', 'Parameter'] != "--None--":
            st.markdown("Domain Filters: `" + _temp_dict.loc['Domain Field', 'Parameter'] + "` = `" + str(_temp_dict.loc['Domains', 'Parameter']) + "`")
        st.markdown("Weight Field: `" + _temp_dict.loc['Weight Field', 'Parameter'] + "`")
        with st.expander("Capping Summary"):
          st.info("## Capping Summary")

          # calculations showed in the screen start here
          cap_obj = pyrpa.capping(samples=smp_obj,
                                  gradefield=_temp_dict.loc['Grade Field', 'Parameter'],
                                  capping_levels=[float(_temp_dict.loc['Low Cap', 'Parameter']),
                                                  float(_temp_dict.loc['Selected Cap', 'Parameter']),
                                                  float(_temp_dict.loc['High Cap', 'Parameter'])],
                                                  unit=gradeunit)

          cap_stats = cap_obj.stats(cap=float(_temp_dict.loc['Selected Cap', 'Parameter'])) # generate the descriptive statistics

          st.dataframe(cap_stats.astype(str),use_container_width=True) # show the descriptive statistics

          labels = ["Uncapped", "Capped"]

          # Create subplots: use 'domain' type for Pie subplot
          fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]]) # make_subplots - plotly command
          fig.add_trace(go.Pie(labels=labels, # add_trace - plotly command
                               values=[cap_stats.loc['Count', 'Capped']-cap_stats.loc['Number Capped', 'Capped'],
                                       cap_stats.loc['Number Capped', 'Capped']],
                               name="Sample Count"), 1, 1)
          fig.add_trace(go.Pie(labels=labels,
                               values=[100.-float(cap_stats.loc['Metal Loss', 'Capped'].strip("%")),
                                                      float(cap_stats.loc['Metal Loss', 'Capped'].strip("%"))],
                               name="Metal"),
                        1, 2)

          # Use `hole` to create a donut-like pie chart
          fig.update_traces(hole=.4, hoverinfo="label+percent+name")

          fig.update_layout(
              # Add annotations in the center of the donut pies.
              annotations=[dict(text='Capped Samples', x=0.15, y=0.5, font_size=10, showarrow=False),
                           dict(text='Metal Loss', x=0.82, y=0.5, font_size=10, showarrow=False)])
          colors = ['#D6F591','#667545']
          fig.update_traces(marker=dict(colors=colors))
          fig.add_annotation(
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            text="SLR CONSULTING",
                            showarrow=False,
                            font=dict(
                                size=50,
                                color="rgba(200, 200, 200, 0.2)"
                            )
                        )
          # output_file = 'pie_chart.png'
          # pio.write_image(fig, output_file, format='png')          # st.write(st.session_state.piechartimage)
          col1,col2,col3 = st.columns([1,3,1])
          with col2:
            st.plotly_chart(fig)

          if print_layout:
              common.make_whitespace(35)
              common.show_header()


        with st.expander("Views"):
          tab1, tab2 = st.tabs(["3D View", "Orthogonal View"])
          with tab1:
            st.info("## 3D View")
            col4,col5,col6 = st.columns([1,6,1])

            mycolors = [uncapped_color, lowcap_color, selectedcap_color, highcap_color]
            fig = px.scatter_3d(smp_obj.data,
                                x=xyzfields[0],
                                y=xyzfields[1],
                                z=xyzfields[2],
                                color='Capping Levels',
                                color_discrete_sequence=mycolors,
                                size='Point Size3D', template='plotly_white')

            fig.update_layout(scene_aspectmode='data')
            # removes the white contour around the points in 3d
            fig.update_traces(marker=dict(line=dict(width=0)))
            fig.update_layout(width=800, height=800)
            fig.add_annotation(
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            text="SLR CONSULTING",
                            showarrow=False,
                            font=dict(
                                size=50,
                                color="rgba(200, 200, 200, 0.2)"
                            )
                        )
            col5.plotly_chart(fig)

            if print_layout:
                common.make_whitespace(40)
                common.show_header()
                common.make_whitespace(2)
        # with st.expander("Orthogonal Data View"):
        with tab2:
          st.info("## Orthogonal Data View")

          if not print_layout:
              xyzplanes = ['Plan View', 'East West', 'North South']
              _temp_dict.loc['XYZ Plane', 'Parameter'] = common.radio(selection=_temp_dict.loc['XYZ Plane', 'Parameter'],
                                                                      options=xyzplanes,
                                                                      display_text="",
                                                                      key='XYZ Plane')

          xmin, xmax = smp_obj.data[xyzfields[0]].min(), smp_obj.data[xyzfields[0]].max()
          ymin, ymax = smp_obj.data[xyzfields[1]].min(), smp_obj.data[xyzfields[1]].max()
          zmin, zmax = smp_obj.data[xyzfields[2]].min(), smp_obj.data[xyzfields[2]].max()

          xrange, yrange, zrange = xmax-xmin, ymax-ymin, zmax-zmin
          xc, yc, zc = xrange/2. + xmin, yrange/2. + ymin, zrange/2. + zmin
          xrange *= 1.1
          yrange *= 1.1
          zrange *= 1.1

          pl_suffix = ''

          if _temp_dict.loc['XYZ Plane', 'Parameter'] == 'Plan View':
              x=xyzfields[0]
              y=xyzfields[1]
              reverse_axis = False
              if xrange > yrange:
                  srange = xrange
              else:
                  srange = yrange
              xmin, ymin = xc - srange/2., yc - srange/2.
              xmax, ymax = xc + srange/2., yc + srange/2.
              pl_suffix = ' - Looking Down'

          if _temp_dict.loc['XYZ Plane', 'Parameter'] == 'East West':
              x = xyzfields[0]
              y = xyzfields[2]
              reverse_axis = False
              if xrange > zrange:
                  srange = xrange
              else:
                  srange = zrange
              xmin, ymin = xc - srange / 2., zc - srange / 2.
              xmax, ymax = xc + srange / 2., zc + srange / 2.
              pl_suffix = ' - Looking South'

          if _temp_dict.loc['XYZ Plane', 'Parameter'] == 'North South':
              x = xyzfields[1]
              y = xyzfields[2]
              reverse_axis = True
              if yrange > zrange:
                  srange = yrange
              else:
                  srange = zrange
              xmin, ymin = yc - srange / 2., zc - srange / 2.
              xmax, ymax = yc + srange / 2., zc + srange / 2.
              pl_suffix = ' - Looking West'

          fig = px.scatter(smp_obj.data,
                           x=x,
                           y=y,
                           color='Capping Levels',
                           color_discrete_sequence=mycolors,
                           size='Point Size')

          fig.update_layout(title=_temp_dict.loc['XYZ Plane', 'Parameter'] + pl_suffix,
                            scene_aspectmode='data',
                            width=800, height=800)
          fig.update_xaxes(range=[xmin, xmax])
          fig.update_yaxes(range=[ymin, ymax])
          fig.update_xaxes(tickangle=90)
          fig.update_traces(marker=dict(line=dict(width=0)))
          fig.add_annotation(
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            text="SLR CONSULTING",
                            showarrow=False,
                            font=dict(
                                size=50,
                                color="rgba(200, 200, 200, 0.2)"
                            )
                        )
          col19,col20,col21 = st.columns([1,6,1])
          col20.plotly_chart(fig)

          if print_layout:
              common.make_whitespace(44)
              common.show_header()
        with st.expander("Decile Analysis"):
          st.info("## Decile Analysis")
          cap_obj.capping_levels =  [float(_temp_dict.loc['Low Cap', 'Parameter']),
                                     float(_temp_dict.loc['Selected Cap', 'Parameter']),
                                     float(_temp_dict.loc['High Cap', 'Parameter'])]
          dec_df = cap_obj.decile_analysis().style.format('{:20,.2f}')
          # st.table(dec_df)
          # AgGrid(dec_df)
          st.dataframe(data=dec_df,use_container_width=True)

          if print_layout:
              common.make_whitespace(30)
              common.show_header()
              common.make_whitespace(2)
        with st.expander("Log Probability Plot"):
          st.info("## Log Probability Plot")
          cap_obj.capping_levels = cap_obj.capping_levels[:-1]
          fig = cap_obj.log_probability_plot(show_caps=True) # log_probability_plot is a function inside of capping.py
          st.pyplot(fig)

          if print_layout:
              common.make_whitespace(35)
              common.show_header()
              common.make_whitespace(5)
        with st.expander("Histogram"):
          st.info("## Histogram")

          if not print_layout:
              _temp_dict.loc['Histogram Bin', 'Parameter'] = float(st.text_input("Histogram Bin",
                                                                             value=_temp_dict.loc['Histogram Bin', 'Parameter']))

          if weightf is None:
              w = None
              ytitle = 'Count'
          else:
              w = smp_obj.data[weightf]
              ytitle = 'Sum of Weights'

          bins = np.arange(0.,
                           smp_obj.data[_temp_dict.loc['Grade Field', 'Parameter']].max() + float(_temp_dict.loc['Histogram Bin', 'Parameter']),
                           float(_temp_dict.loc['Histogram Bin', 'Parameter']))
          y, x = np.histogram(smp_obj.data[_temp_dict.loc['Grade Field', 'Parameter']],
                              weights=w,
                              bins=bins)
          x += float(_temp_dict.loc['Histogram Bin', 'Parameter'])/2.
          histdata = pd.DataFrame({'x': x[:-1], 'y': y})

          if float(_temp_dict.loc['Histogram X Max', 'Parameter']) == -99.:
              _temp_dict.loc['Histogram X Max', 'Parameter'] = smp_obj.data[
                  _temp_dict.loc['Grade Field', 'Parameter']].max()
              _temp_dict.loc['Histogram Y Max', 'Parameter'] = np.max(y)

          if not print_layout:

              _temp_dict.loc['Histogram X Max', 'Parameter'] = st.text_input("Histogram X Max",
                                                                             value=_temp_dict.loc['Histogram X Max', 'Parameter'],
                                                                             key='Histogram X Max')

              _temp_dict.loc['Histogram Y Max', 'Parameter'] = st.text_input("Histogram Y Max",
                                                                             value=_temp_dict.loc[
                                                                                 'Histogram Y Max', 'Parameter'],
                                                                             key='Histogram Y Max')

              # _temp_dict.loc['Histogram X Max', 'Parameter'] = st.slider("Histogram X Max",
              #                                                            0.,
              #                                                            float(smp_obj.data[_temp_dict.loc['Grade Field', 'Parameter']].max()),
              #                                                            float(_temp_dict.loc['Histogram X Max', 'Parameter']),
              #                                                            1., key='Histogram X Max')
              # _temp_dict.loc['Histogram Y Max', 'Parameter'] = st.slider("Histogram Y Max",
              #                                                            0.,
              #                                                            float(np.max(y)),
              #                                                            float(_temp_dict.loc['Histogram Y Max', 'Parameter']),
              #                                                            1., key='Histogram Y Max')

          fig = px.bar(histdata, x='x', y='y', template="plotly_white")
          fig['layout']['xaxis'].update(title=_temp_dict.loc['Grade Field', 'Parameter'] + ' '+ gradeunit, range=[0, _temp_dict.loc['Histogram X Max', 'Parameter']], autorange=False)
          fig['layout']['yaxis'].update(title=ytitle, range=[0, _temp_dict.loc['Histogram Y Max', 'Parameter']], autorange=False)
          col7,col8,col9 = st.columns([1,6,1])
          fig.update_layout(width=700, height=500)
          fig.update_traces(marker_color='#667545')
          fig.add_annotation(
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            text="SLR CONSULTING",
                            showarrow=False,
                            font=dict(
                                size=50,
                                color="rgba(200, 200, 200, 0.2)"
                            )
                        )

          with col8:
            st.plotly_chart(fig)

          if print_layout:
              common.make_whitespace(40)
              common.show_header()
              common.make_whitespace(5)
        with st.expander("Disintegration Analysis"):
          st.info("## Disintegration Analysis")
          col10,col11,col12 = st.columns([1,6,3])
          smp_obj.data["Metal Disintegration (1.0 - g(x)/g(x-1)*100)"] = cap_obj.disintegration_analysis()
          smp_obj.data['Disint_color'] = 0.
          smp_obj.data['Disint_color'][smp_obj.data["Metal Disintegration (1.0 - g(x)/g(x-1)*100)"]>15] = 1.
          fig = px.scatter(smp_obj.data.loc[int(len(smp_obj.data)*0.9):],
                        x=_temp_dict.loc['Grade Field', 'Parameter'] ,
                        y="Metal Disintegration (1.0 - g(x)/g(x-1)*100)",
                        color='Capping Levels',
                        color_discrete_sequence=mycolors,
                        size='Point Size')
          fig.update_layout(xaxis_type="log")
          fig['layout']['xaxis'].update(title=_temp_dict.loc['Grade Field', 'Parameter'] + ' '+ gradeunit)
          fig.update_traces(marker=dict(line=dict(width=0)))
          fig.update_layout(width=900,height=600)
          fig.add_annotation(
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            text="SLR CONSULTING",
                            showarrow=False,
                            font=dict(
                                size=50,
                                color="rgba(200, 200, 200, 0.2)"
                            )
                        )
          with col11:
            st.plotly_chart(fig)

          if print_layout:
              common.make_whitespace(40)
              common.show_header()
              common.make_whitespace(5)
              st.info("## Parameters")
              st.dataframe(_temp_dict,use_container_width=True)

          _temp_dict.to_csv('_temp_cap_dict')
        # text = ""
        # with st.expander("Reporting"):
        #   st.info('## Reporting') 
        #   introduction = st.text_area('Introduction Key points', ' Write a brief introduction here or bullet points and the AI assitant will generate rich text for you')  
        #   openai.api_key = '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'
        #   if st.button('Generate Rich Content'):
        #     completion = openai.ChatCompletion.create(
        #                                           model="gpt-3.5-turbo",
        #                                           messages=[
        #                                             {"role": "user", "content": "generate an introduction for mineral resource estimation grade capping analysis done by SLR consulting for the project "+ ProjectName +" using these information (make the text richer) : " + introduction}
        #                                           ]
        #                                         )

        #     st.session_state.AI_Intorduction = st.text_area('Introduction AI suggestion',completion.choices[0].message['content'])
        #   if st.button('Export Report'):
        #     # st.write(st.session_state.AI_Intorduction)
        #     context = {'project_name':ProjectName,
        #                 'piechart':InlineImage(doc,st.session_state.piechartimage,width=Mm(160), height=Mm(80))}
        #     doc.render(context)
        #     doc.save('Exported_report.docx')
        #       #st.success('Report generated successfully')