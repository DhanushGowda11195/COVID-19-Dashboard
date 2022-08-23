#!/usr/bin/env python
# coding: utf-8

# In[291]:


import pandas as pd
import numpy as np
import datetime
import requests
import json
import dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from urllib.request import urlopen
import re
import calendar
import time
pd.set_option('mode.chained_assignment', None)

# In[292]:


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server=app.server

# In[293]:


def No_Data_Available():
    fig=go.Figure()
    fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',
                      font=dict(color='white'),annotations=[{"text": "No Data Available","xref": "paper","yref": "paper",
                        "showarrow": False,"font": {"size": 28}}])
    fig.update_xaxes(showgrid=False,zeroline=False,showticklabels=False,visible=False)
    fig.update_yaxes(showgrid=False,zeroline=False,showticklabels=False,visible=False)
    return fig


# In[294]:


# Fetching GeoJson for all Countries

with urlopen('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json') as response:
    countries = json.load(response)

# Country Codes and Country Names

Country_ISO=pd.read_excel('Country_ISO.xlsx')

# Reading the Data

Day_Wise=pd.read_csv('global_covid_raw.csv')
Day_Wise['Date']=pd.to_datetime(Day_Wise['Date'])

# Global Daily Dataset

Day_Wise_Global=Day_Wise.groupby(['Year','Month','Week','Date']).sum().reset_index()

# Calculating the last available Recovered and Vaccine Data

ddf1=Day_Wise.loc[Day_Wise.Recovered!=0]
ddf1=ddf1.loc[ddf1.groupby(['Country'])['Date'].idxmax(),['Country','Date','Recovered']]
ddf1['Recovered Modified']=ddf1['Recovered'].astype(str)+' as on (' + ddf1['Date'].dt.strftime('%Y-%m-%d') +')'
ddf2=Day_Wise.loc[Day_Wise['Total Vaccinations']!=0]
ddf2=ddf2.loc[ddf2.groupby(['Country'])['Date'].idxmax(),['Country','Date','Total Vaccinations']]
ddf2['Total Vaccinations Modified']=ddf2['Total Vaccinations'].astype(str)+' as on (' + ddf2['Date'].dt.strftime('%Y-%m-%d') +')'

# Global Dataset for the Latest Date

Global=Day_Wise.loc[Day_Wise.Date==Day_Wise['Date'].max(),['Country','Code','Date','Week','Month', 'Year',
                                                           'Confirmed', 'Deaths']].reset_index().drop('index',axis=1)
Global=Global.merge(ddf1[['Country','Recovered','Recovered Modified']],how='left',on='Country').fillna(0)
Global=Global.merge(ddf2[['Country','Total Vaccinations','Total Vaccinations Modified']],how='left',on='Country').fillna(0)
Global[['Recovered','Total Vaccinations']]=Global[['Recovered','Total Vaccinations']].astype('int64')

# Total Global Count

Global_Count=pd.DataFrame(Day_Wise_Global[['Date','Confirmed','Deaths','Total Vaccinations']].loc[Day_Wise_Global.Date==Day_Wise_Global.Date.max()].stack().astype(str).reindex()).reset_index().drop('level_0',axis=1).drop(0)
Global_Count.columns=['Last Refreshed',Day_Wise_Global['Date'].max().date().strftime('%d-%m-%Y')]
Global_Count[Day_Wise_Global['Date'].max().date().strftime('%d-%m-%Y')]=pd.to_numeric(Global_Count[Day_Wise_Global['Date'].max().date().strftime('%d-%m-%Y')])

# Top 10 Affected Countries

Top10=Global.sort_values('Confirmed',ascending=False,ignore_index=True)[:10].drop(['Date','Week','Month','Year',
                                                                                  'Recovered Modified','Total Vaccinations Modified'],axis=1)

Last_Refreshed_Global=Day_Wise_Global['Date'].max().date().strftime('%d-%m-%Y')


# In[295]:


# Fetching GeoJson for India

India_GeoJson=json.load(open('states_india.geojson','r'))

# India and State Wise Dataset for all Days

df=pd.read_csv('india_covid_raw.csv')
df['Date']=pd.to_datetime(df['Date'])
India=df[['Date','Week','Month','Year','Confirmed', 'Recovered', 'Deaths','Active']].groupby(['Date','Week','Month','Year']).sum().reset_index()

States=df.loc[df.State!='Ladakh']
DateRange=[States['Date'].min()+datetime.timedelta(days=x) for x in range((States['Date'].max()-States['Date'].min()).days+1)]

State_ID={}
for feature in India_GeoJson['features']:
    feature['id']=feature['properties']['state_code']
    State_ID[feature['properties']['st_nm']]=feature['id']
States['ID']=States.State.apply(lambda x: State_ID[x])

# Top 10 Worst Affected Sates

IndiaTop10=States.loc[States.Date==States.Date.max()]
IndiaTop10=IndiaTop10.sort_values('Active',ascending=False,ignore_index=True)[:10]

IndiaTop10=IndiaTop10[['State','Confirmed','Active','Recovered','Deaths']]

# India Count

India_Count=India[['Date','Confirmed','Recovered','Deaths','Active']].loc[India.Date==India.Date.max()]
India_Count=India_Count[['Confirmed','Active','Recovered','Deaths']].replace('Date','Last Refreshed')
India_Count=India_Count.stack().astype(str).reindex()
India_Count=pd.DataFrame(India_Count).reset_index().drop('level_0',axis=1)
India_Count.columns=['Last Refreshed',India.Date.max().strftime('%d-%m-%y')]
India_Count[India.Date.max().strftime('%d-%m-%y')]=pd.to_numeric(India_Count[India.Date.max().strftime('%d-%m-%y')])

# India New Cases

Latest=(States[['Date','Confirmed','Recovered','Deaths','State']].loc[States.Date==States['Date'].max()]).drop(labels=['Date'],axis=1)
Old=(States[['Date','Confirmed','Recovered','Deaths','State']].loc[States.Date==States['Date'].max()-datetime.timedelta(days=1)]).drop(labels=['Date'],axis=1)
IndiaNewCases=Latest.set_index(['State']).subtract(Old.set_index(['State'])).reset_index()
IndiaNewCases['Active']=IndiaNewCases['Confirmed']-IndiaNewCases['Recovered']-IndiaNewCases['Deaths']
IndiaNewCases.drop(['Confirmed'],axis=1,inplace=True)
StateList=[x for x in IndiaNewCases['State']]

Last_Refreshed_India=India.Date.max().strftime('%d-%m-%y')


# In[296]:


Vaccine=pd.read_csv('india_vaccine.csv')

Vaccine['Date']=pd.to_datetime(Vaccine['Date'])
Vaccine_India=Vaccine.groupby(['Date','Week','Month','Year']).sum().reset_index()

Vaccine_States=Vaccine.loc[Vaccine.State!='Ladakh']
DateRange=[Vaccine_States['Date'].min()+datetime.timedelta(days=x) for x in range((Vaccine_States['Date'].max()-Vaccine_States['Date'].min()).days+1)]

State_ID={}
for feature in India_GeoJson['features']:
    feature['id']=feature['properties']['state_code']
    State_ID[feature['properties']['st_nm']]=feature['id']
Vaccine_States['ID']=Vaccine_States.State.apply(lambda x: State_ID[x])

# Top 10 Worst Affected Sates

Vaccine_IndiaTop10=Vaccine_States.loc[Vaccine_States.Date==Vaccine_States.Date.max()]
Vaccine_IndiaTop10=Vaccine_IndiaTop10.sort_values('Total Doses',ascending=False,ignore_index=True)[:10]

Vaccine_IndiaTop10=Vaccine_IndiaTop10[['State','18+ Total Doses','15-18 Total Doses','12-14 Total Doses','Booster Total Doses']]

# India Count

Vaccine_India_Count=Vaccine_India[['Date','18+ Total Doses','15-18 Total Doses','12-14 Total Doses','Booster Total Doses']].loc[Vaccine_India.Date==Vaccine_India.Date.max()]
Vaccine_India_Count=Vaccine_India_Count[['18+ Total Doses','15-18 Total Doses','12-14 Total Doses','Booster Total Doses']].replace('Date','Last Refreshed')
Vaccine_India_Count=Vaccine_India_Count.stack().astype(str).reindex()
Vaccine_India_Count=pd.DataFrame(Vaccine_India_Count).reset_index().drop('level_0',axis=1)
Vaccine_India_Count.columns=['Last Refreshed',Vaccine_India.Date.max().strftime('%d-%m-%y')]
Vaccine_India_Count[Vaccine_India.Date.max().strftime('%d-%m-%y')]=pd.to_numeric(Vaccine_India_Count[Vaccine_India.Date.max().strftime('%d-%m-%y')])

# India New Cases

Vaccine_Latest=(Vaccine_States[['Date','18+ Total Doses','15-18 Total Doses','12-14 Total Doses','Booster Total Doses','State']].loc[Vaccine_States.Date==Vaccine_States['Date'].max()]).drop(labels=['Date'],axis=1)
Vaccine_Old=(Vaccine_States[['Date','18+ Total Doses','15-18 Total Doses','12-14 Total Doses','Booster Total Doses','State']].loc[Vaccine_States.Date==Vaccine_States['Date'].max()-datetime.timedelta(days=1)]).drop(labels=['Date'],axis=1)
Vaccine_IndiaNewCases=Vaccine_Latest.set_index(['State']).subtract(Vaccine_Old.set_index(['State'])).reset_index()
Vaccine_StateList=[x for x in Vaccine_IndiaNewCases['State']]

Vaccine_Last_Refreshed_India=Vaccine_India.Date.max().strftime('%d-%m-%y')


# In[297]:


# Styling 

Title={'backgroundColor':'#000000','color':'#FFFFFF','textAlign':'center','font-weight':'bold'}

Tab_Style={'backgroundColor': '#000000','border':'none','padding': '6px','fontWeight': 'bold','color': 'white'}

Tab_Selected_Style={'borderTop': '4px solid #0000FF','borderBottom': '1px solid black','borderLeft': '1px solid black',
    'borderRight': '1px solid black','backgroundColor': '#1F1F1F','color': 'white','padding': '6px'}

Main_Tab={'height': '44px'}

Web_Layout_Style={'backgroundColor':'#000000','margin':'5px'}
Heading={'backgroundColor':'#000000','color':'#FFFFFF','textAlign':'center','font-weight':'bold'}
Page_Background='#000000'
Data_Table_Header_Style={'backgroundColor': 'rgb(30, 30, 30)'}
Data_Table_Cell_Style={'backgroundColor': 'rgb(50, 50, 50)','color': 'white','fontWeight': 'bold','font_family': 'cursive',
                       'font_size': '14px','text_align': 'center'}

Grid_Color='#121212'
Fig_Font=dict(color='white')
Title_Font={'size':14,'color':'white'}
Tick_Font={'color':'white','size':12}
Page_Background='#000000'
Fig_Title_Font=dict(color='white',size=16)

Plot_Colors1={'Active':'yellow','Recovered':'green','Deaths':'red','Total Vaccinations':'orange',
             'Total Doses':'#007f5f','18+ Total Doses':'#2b9348','15-18 Total Doses':'#55a630','12-14 Total Doses':'#80b918','Booster Total Doses':'#ff8500'}
Plot_Colors2={'Average_Active':'#29bf12','Maximum_Active':'#abff4f','7_Day_Simple_Moving_Average_Active':'#08bdbd',
              '7_Day_Exponential_Moving_Average_Active':'#f21b3f',
             'Average_Deaths':'#ff9914','Maximum_Deaths':'#5fad56','7_Day_Simple_Moving_Average_Deaths':'#f78154',
              '7_Day_Exponential_Moving_Average_Deaths':'#4d9078',
             'Average_Recovered':'#b4436c','Maximum_Recovered':'#064789','7_Day_Simple_Moving_Average_Recovered':'#ffd97d',
              '7_Day_Exponential_Moving_Average_Recovered':'#56282d',
             'Average_Total Vaccinations':'#ff4500','Maximum_Total Vaccinations':'#c46210','7_Day_Simple_Moving_Average_Total Vaccinations':'#c0362c',
              '7_Day_Exponential_Moving_Average_Total Vaccinations':'#ff4f00',
              '7_Day_Simple_Moving_Average_18+ Total Doses':'#a3f7b5',
       '7_Day_Simple_Moving_Average_15-18 Total Doses':'#72e0ac',
       '7_Day_Simple_Moving_Average_12-14 Total Doses':'#51bea1',
       '7_Day_Simple_Moving_Average_Booster Total Doses':'#42a59f',
       '7_Day_Simple_Moving_Average_Total Doses':'#073b3a',
        'Average_18+ Total Doses':'#0b6e4f',
       'Average_15-18 Total Doses':'#08a045', 'Average_12-14 Total Doses':'#6bbf59',
       'Average_Booster Total Doses':'#22577a', 'Average_Total Doses':'#38a3a5',
       'Maximum_18+ Total Doses':'#57cc99', 'Maximum_15-18 Total Doses':'#80ed99',
       'Maximum_12-14 Total Doses':'#157a6e', 'Maximum_Booster Total Doses':'#499f68',
       'Maximum_Total Doses':'#77b28c',
       '7_Day_Exponential_Moving_Average_18+ Total Doses':'#c2c5bb',
       '7_Day_Exponential_Moving_Average_15-18 Total Doses':'#93b48b',
       '7_Day_Exponential_Moving_Average_12-14 Total Doses':'#32a287',
       '7_Day_Exponential_Moving_Average_Booster Total Doses':'#09814a',
       '7_Day_Exponential_Moving_Average_Total Doses':'#bcb382'}


# In[298]:


# Global PLot

def Global_Plot():
    fig = px.choropleth_mapbox(Global, geojson=countries, locations='Code', color='Confirmed',
                           color_continuous_scale=['#ff0000','#bf0000','#800000','#400000'],
                           mapbox_style='carto-darkmatter',
                           hover_name='Country',
                           hover_data=['Confirmed','Recovered Modified','Deaths', 'Total Vaccinations'],
                           zoom=2.5,center = {"lat": 24, "lon": 78},
                           )
    fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,height=550,margin=dict(l=0, r=0, t=0, b=0))
    return fig

# Global Count

def Global_Count_Plot():
    x=[x for x in Global_Count['Last Refreshed']]
    y=[x for x in Global_Count[Global_Count.columns[1]]]


    fig=go.Figure([go.Bar(y=[x[2]],name='Total Vaccinations',marker_color='green',showlegend=False,x=[y[2]],width=0.25,orientation='h',hoverinfo='none'),
                   go.Bar(y=[x[1]],name='Deaths',marker_color='red',showlegend=False,x=[y[1]],width=0.25,orientation='h',hoverinfo='none'),
                   go.Bar(y=[x[0]],name='Conifrmed',marker_color='blue',showlegend=False,x=[y[0]],width=0.25,orientation='h',hoverinfo='none')])
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,height=110,width=260,
                      margin= {'l': 0, 'r': 0, 't': 0, 'b': 0})
    return fig


# In[299]:


# India Map

def India_Plot():
    Indian_Map=States.loc[States.Date==States.Date.max()]
    fig=px.choropleth_mapbox(Indian_Map,geojson=India_GeoJson,locations='ID',color='Confirmed',mapbox_style='carto-darkmatter',
                            hover_name='State', hover_data=['Confirmed','Recovered','Deaths'],zoom=3.5,center = {"lat": 24, "lon": 78}
                             ,color_continuous_scale=['#ff0000','#bf0000','#800000','#400000'])
    fig.update_geos(fitbounds='locations',visible=False)
    fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,height=550,margin=dict(l=0, r=0, t=0, b=0))
    return fig

# India Count

def India_Count_Plot():
    x=[x for x in India_Count['Last Refreshed']]
    y=[x for x in India_Count[India_Count.columns[1]]]


    fig=go.Figure([go.Bar(y=[x[3]],name='Deaths',marker_color='red',showlegend=False,x=[y[3]],width=0.25,orientation='h'),
                   go.Bar(y=[x[2]],name='Recovered',marker_color='green',showlegend=False,x=[y[2]],width=0.25,orientation='h'),
                   go.Bar(y=[x[1]],name='Active',marker_color='yellow',showlegend=False,x=[y[1]],width=0.25,orientation='h'),
                   go.Bar(y=[x[0]],name='Conifrmed',marker_color='blue',showlegend=False,x=[y[0]],width=0.25,orientation='h')])
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,height=125,width=260,
                      margin= {'l': 0, 'r': 0, 't': 0, 'b': 0})
    return fig


# In[300]:


# India Vaccine Map

def Vaccine_India_Plot():
    Vaccine_Indian_Map=Vaccine_States.loc[Vaccine_States.Date==Vaccine_States.Date.max()]
    fig=px.choropleth_mapbox(Vaccine_Indian_Map,geojson=India_GeoJson,locations='ID',color='Total Doses',mapbox_style='carto-darkmatter',
                            hover_name='State', hover_data=['18+ Total Doses','15-18 Total Doses','12-14 Total Doses','Booster Total Doses','Total Doses'],zoom=3.5,center = {"lat": 24, "lon": 78}
                             ,color_continuous_scale=['#007f5f','#2b9348','#55a630','#80b918'])
    fig.update_geos(fitbounds='locations',visible=False)
    fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,height=550,margin=dict(l=0, r=0, t=0, b=0))
    return fig

# India Count

def Vaccine_India_Count_Plot():
    x=[x for x in Vaccine_India_Count['Last Refreshed']]
    y=[x for x in Vaccine_India_Count[Vaccine_India_Count.columns[1]]]


    fig=go.Figure([go.Bar(y=[x[3]],name='Booster Total Doses',marker_color='#80b918',showlegend=False,x=[y[3]],width=0.25,orientation='h'),
                   go.Bar(y=[x[2]],name='12-14 Total Doses',marker_color='#55a630',showlegend=False,x=[y[2]],width=0.25,orientation='h'),
                   go.Bar(y=[x[1]],name='15-18 Total Doses',marker_color='#2b9348',showlegend=False,x=[y[1]],width=0.25,orientation='h'),
                   go.Bar(y=[x[0]],name='18+ Total Doses',marker_color='#007f5f',showlegend=False,x=[y[0]],width=0.25,orientation='h')])
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,height=125,width=260,
                      margin= {'l': 0, 'r': 0, 't': 0, 'b': 0})
    return fig


# In[301]:


# Layout

app.layout=html.Div([
    html.Div(
        html.H1('COVID-19 DASHBOARD',
                style=Title),
        className='row'),
    html.Div([
        dcc.Tabs(id='Layout',
                 value='Tab1',
                 style=Main_Tab,
                 children=[
                     dcc.Tab(id='Global',
                             label='GLOBAL',
                             value='Tab1',
                             style=Tab_Style,
                             selected_style=Tab_Selected_Style,
                             className='custom-tab',
                             selected_className='custom-tab--selected',
                             children=[
                                 html.Div([
                                     html.Div([
                                         html.Div(
                                             html.H6('GLOBAL STATS',
                                                     style=Heading),
                                             className='row'),
                                         html.Div([
                                             html.Div([
                                                 dash_table.DataTable(id='Global_Count',
                                                                      columns=[{'name': 'Last Refreshed', 
                                                                                'id': 'Last Refreshed'}, 
                                                                               {'name': Last_Refreshed_Global,
                                                                                'id':Last_Refreshed_Global}],
                                                                      data=Global_Count.to_dict('records'),
                                                                      style_table={'overflowY': 'auto'},
                                                                      style_header=Data_Table_Header_Style,
                                                                      style_cell=Data_Table_Cell_Style,
                                                                      style_cell_conditional=[{'if':
                                                                                               {'column_id':'Last Refreshed'},
                                                                                               'textAlign':'left'},
                                                                                              {'if':
                                                                                               {'column_id':Last_Refreshed_Global},
                                                                                               'textAlign':'right'}])
                                             ],className='six columns',style=Web_Layout_Style),
                                             html.Div([
                                                 html.Br(),
                                                 dcc.Graph(id='Global_Count_Plot',
                                                           figure=Global_Count_Plot(),
                                                           config = {'displayModeBar': False})
                                             ],className='four columns',style=Web_Layout_Style)
                                         ],className='row',style=Web_Layout_Style),
                                         html.Div(
                                             html.H6('TOP 10 AFFECTED COUNTRIES',
                                                     style=Heading),
                                             className='row',style=Web_Layout_Style),
                                         html.Div(
                                             dash_table.DataTable(id='Top_10',
                                                                  columns=[{'name': i, 'id': i} for i in Top10.columns],
                                                                  data=Top10.to_dict('records'),
                                                                  style_table={'overflowY': 'auto'},
                                                                  sort_action='native',sort_mode='multi',
                                                                  style_header=Data_Table_Header_Style,
                                                                  style_cell=Data_Table_Cell_Style,
                                                                  style_cell_conditional=[{'if':
                                                                                           {'column_id':'Country'},
                                                                                           'textAlign':'left'}]),
                                             className='row',style=Web_Layout_Style)
                                     ],className='four columns',style=Web_Layout_Style),
                                     html.Div([
                                         html.Div(
                                             html.H6('GLOBAL CASES',
                                                     style=Heading),
                                             className='row',style=Web_Layout_Style),
                                         html.Div(
                                             dcc.Graph(id='Global_Plot',
                                                       figure=Global_Plot()))
                                     ],className='eight columns',style=Web_Layout_Style)
                                 ],className='row',style=Web_Layout_Style),
                                 html.Div([
                                     html.Div(
                                             dcc.DatePickerRange(
                                                 id='Global_Date_Filter',
                                                 min_date_allowed=datetime.datetime(2020,1,1),
                                                 max_date_allowed=datetime.datetime.today().date(),
                                                 initial_visible_month=datetime.datetime.today().date()),
                                             className='three columns',style=Web_Layout_Style),
                                         html.Div(
                                             dcc.Dropdown(id='Global_Quick_Date_Filter',
                                                          options=[
                                                              {'label':'Week to Date','value':'Week to Date'},
                                                              {'label':'Previous Week','value':'Previous Week'},
                                                              {'label':'Last 7 Days','value':'Last 7 Days'},
                                                              {'label':'Month to Date','value':'Month to Date'},
                                                              {'label':'Previous Month','value':'Previous Month'},
                                                              {'label':'Last 30 Days','value':'Last 30 Days'},
                                                              {'label':'Year to Date','value':'Year to Date'},
                                                              {'label':'Previous Year','value':'Previous Year'},
                                                              {'label':'All Time','value':'All Time'}],
                                                          value='All Time',
                                                          clearable=False,
                                                          multi=False,
                                                          placeholder='Select Date Range'),
                                             className='two columns',style=Web_Layout_Style),
                                         html.Div(
                                             dcc.Dropdown(id='Global_Span',
                                                          options=[
                                                              {'label':'Daily','value':'Date'},
                                                              {'label':'Weekly','value':'Week'},
                                                              {'label':'Monthly','value':'Month'},
                                                              {'label':'Yearly','value':'Year'}],
                                                          value='Date',
                                                          clearable=False,
                                                          multi=False),
                                             className='one columns',style=Web_Layout_Style),
                                     html.Div(
                                         dcc.Dropdown(id='Global_Category',
                                                          options=[
                                                              {'label':'Active','value':'Active'},
                                                              {'label':'Recovered','value':'Recovered'},
                                                              {'label':'Deaths','value':'Deaths'},
                                                              {'label':'Vaccination','value':'Total Vaccinations'}],
                                                          value=['Active'],
                                                          clearable=True,
                                                          multi=True),
                                             className='two columns',style=Web_Layout_Style),
                                     html.Div(
                                         dcc.Dropdown(id='Global_Type',
                                                     options=[
                                                         {'label':'Average','value':'Average_'},
                                                         {'label':'7_Day Simple Moving Average','value':'7_Day_Simple_Moving_Average_'},
                                                         {'label':'7_Day Exponential Moving Average','value':'7_Day_Exponential_Moving_Average_'},
                                                         {'label':'Maximum','value':'Maximum_'}],
                                                      value=['Average_','Maximum_'],
                                                      clearable=True,
                                                      multi=True),
                                              className='four columns',style=Web_Layout_Style),
                                     html.Div(
                                             dcc.Dropdown(id='Global_Scale',
                                                          options=[
                                                              {'label':'Linear','value':'linear'},
                                                              {'label':'Log','value':'log'}],
                                                          value='linear',
                                                          clearable=False,
                                                          multi=False),
                                             className='one columns',style=Web_Layout_Style),
                                 ],className='row',style=Web_Layout_Style),
                                 html.Div(
                                     html.H6('GLOBAL TRENDLINE',
                                             style=Heading),
                                     className='row',style=Web_Layout_Style),
                                 html.Div([
                                     dcc.Graph(id='Global_Trendline')
                                 ],className='row',style=Web_Layout_Style),
                                 html.Div([
                                     html.Div(html.H6('COUNTRY WISE TRENDLINE & LATEST CASE COUNT',
                                                      style=Heading),
                                              className='row',style=Web_Layout_Style),
                                     html.Div(
                                         html.Div(
                                             dcc.Dropdown(id='Country_List',
                                                          options=[{'label':x,'value':x} for x in Country_ISO['Country']],
                                                          value='USA',
                                                          multi=False,
                                                          clearable=False),
                                         className='three columns',style=Web_Layout_Style),
                                     className='row',style=Web_Layout_Style),
                                     html.Div([
                                         html.Div(
                                             dcc.Graph(id='Country_Wise_Trendline'),
                                             className='six columns',style=Web_Layout_Style),
                                         html.Div([
                                             dcc.Graph(id='Country_Wise_New_Case')
                                         ],className='six columns',style=Web_Layout_Style)
                                     ],className='row',style=Web_Layout_Style)
                                 ],className='row',style=Web_Layout_Style),
                                 html.Div(
                                     html.H6('TOP 10 COUNTRIES WITH HIGHEST ACTIVE CASES',
                                             style=Heading),className='row',style=Web_Layout_Style),
                                 html.Div([
                                     dcc.Graph(id='Top_10_Countries')
                                 ],className='row',style=Web_Layout_Style)
                             ]),
                     dcc.Tab(id='India',
                             label='INDIA',
                             value='Tab2',
                             style=Tab_Style,
                             selected_style=Tab_Selected_Style,
                             className='custom-tab',
                             selected_className='custom-tab--selected',
                             children=[
                                 html.Div([
                                    dcc.Tabs(id='Sub_Layout',
                                             value='Tab2-1',
                                             style=Main_Tab,
                                             children=[
                                                 dcc.Tab(id='India_Cases',
                             label='COVID-19 Cases',
                             value='Tab2-1',
                             style=Tab_Style,
                             selected_style=Tab_Selected_Style,
                             className='custom-tab',
                             selected_className='custom-tab--selected',
                             children=[
                                 html.Div([
                                     html.Div([
                                         html.Div(html.H6('INDIA STATS',style=Heading),className='row'),
                                         html.Div([
                                             html.Div([
                                                 dash_table.DataTable(id='IndiaCount',
                                                                      columns=[{'name': 'Last Refreshed', 'id': 'Last Refreshed'}, 
                                                                               {'name': Last_Refreshed_India, 'id':Last_Refreshed_India}],
                                                                      data=India_Count.to_dict('records'),
                                                                      style_table={'overflowY': 'auto'},
                                                                      style_header=Data_Table_Header_Style,
                                                                      style_cell=Data_Table_Cell_Style,
                                                                      style_cell_conditional=[{'if':
                                                                                               {'column_id':'Last Refreshed'},
                                                                                               'textAlign':'left'},
                                                                                              {'if':
                                                                                               {'column_id':Last_Refreshed_India},
                                                                                               'textAlign':'right'}])
                                             ],className='six columns',style=Web_Layout_Style),
                                             html.Div([
                                                 html.Br(),
                                                 dcc.Graph(id='India_Count_Plot',
                                                           figure=India_Count_Plot(),
                                                           config = {'displayModeBar': False})
                                             ],className='four columns',style=Web_Layout_Style)
                                         ],className='row',style=Web_Layout_Style),
                                         html.Div(
                                             html.H6('TOP 10 AFFECTED STATES',
                                                     style=Heading),
                                             className='row',style=Web_Layout_Style),
                                         html.Div(
                                             dash_table.DataTable(id='IndiaTop10',
                                                                  columns=[{'name': i, 'id': i} for i in IndiaTop10.columns],
                                                                  data=IndiaTop10.to_dict('records'),
                                                                  style_table={'overflowY': 'auto'},
                                                                  sort_action='native',
                                                                  sort_mode='multi',
                                                                  style_header=Data_Table_Header_Style,
                                                                  style_cell=Data_Table_Cell_Style,
                                                                  style_cell_conditional=[{'if':
                                                                                           {'column_id':'State'},
                                                                                           'textAlign':'left'}
                                                                                         ]
                                                                 ),className='row',style=Web_Layout_Style)
                                     ],className='four columns',style=Web_Layout_Style),
                                     html.Div([
                                         html.Div(
                                             html.H6('INDIA CASES',
                                                     style=Heading),className='row',style=Web_Layout_Style),
                                         html.Div(
                                             dcc.Graph(id='India_Plot',
                                                       figure=India_Plot()))
                                     ],className='eight columns',style=Web_Layout_Style)
                                 ],className='row',style=Web_Layout_Style),
                                 html.Div([
                                     html.Div(
                                             dcc.DatePickerRange(
                                                 id='India_Date_Filter',
                                                 min_date_allowed=datetime.datetime(2020,1,1),
                                                 max_date_allowed=datetime.datetime.today().date(),
                                                 initial_visible_month=datetime.datetime.today().date()),
                                             className='three columns',style=Web_Layout_Style),
                                         html.Div(
                                             dcc.Dropdown(id='India_Quick_Date_Filter',
                                                          options=[
                                                              {'label':'Week to Date','value':'Week to Date'},
                                                              {'label':'Previous Week','value':'Previous Week'},
                                                              {'label':'Last 7 Days','value':'Last 7 Days'},
                                                              {'label':'Month to Date','value':'Month to Date'},
                                                              {'label':'Previous Month','value':'Previous Month'},
                                                              {'label':'Last 30 Days','value':'Last 30 Days'},
                                                              {'label':'Year to Date','value':'Year to Date'},
                                                              {'label':'Previous Year','value':'Previous Year'},
                                                              {'label':'All Time','value':'All Time'}],
                                                          value='All Time',
                                                          clearable=False,
                                                          multi=False,
                                                          placeholder='Select Date Range'),
                                             className='two columns',style=Web_Layout_Style),
                                         html.Div(
                                             dcc.Dropdown(id='India_Span',
                                                          options=[
                                                              {'label':'Daily','value':'Date'},
                                                              {'label':'Weekly','value':'Week'},
                                                              {'label':'Monthly','value':'Month'},
                                                              {'label':'Yearly','value':'Year'}],
                                                          value='Date',
                                                          clearable=False,
                                                          multi=False),
                                             className='one columns',style=Web_Layout_Style),
                                     html.Div(
                                         dcc.Dropdown(id='India_Category',
                                                          options=[
                                                              {'label':'Active','value':'Active'},
                                                              {'label':'Recovered','value':'Recovered'},
                                                              {'label':'Deaths','value':'Deaths'}],
                                                          value=['Active'],
                                                          clearable=True,
                                                          multi=True),
                                             className='two columns',style=Web_Layout_Style),
                                     html.Div(
                                         dcc.Dropdown(id='India_Type',
                                                     options=[
                                                         {'label':'Average','value':'Average_'},
                                                         {'label':'7_Day Simple Moving Average','value':'7_Day_Simple_Moving_Average_'},
                                                         {'label':'7_Day Exponential Moving Average','value':'7_Day_Exponential_Moving_Average_'},
                                                         {'label':'Maximum','value':'Maximum_'}],
                                                      value=['Average_','Maximum_'],
                                                      clearable=True,
                                                      multi=True),
                                              className='four columns',style=Web_Layout_Style),
                                     html.Div(
                                             dcc.Dropdown(id='India_Scale',
                                                          options=[
                                                              {'label':'Linear','value':'linear'},
                                                              {'label':'Log','value':'log'}],
                                                          value='linear',
                                                          clearable=False,
                                                          multi=False),
                                             className='one columns',style=Web_Layout_Style),
                                 ],className='row',style=Web_Layout_Style),
                                 html.Div(
                                     html.H6('INDIA TRENDLINE',
                                             style=Heading),className='row',style=Web_Layout_Style),
                                 html.Div([
                                     dcc.Graph(id='India_Trendline')
                                 ],className='row',style=Web_Layout_Style),
                                 html.Div([
                                     html.Div(
                                         html.H6('STATE WISE TRENDLINE & LATEST CASE COUNT',
                                                 style=Heading),className='row',style=Web_Layout_Style),
                                     html.Div(
                                         html.Div(
                                             dcc.Dropdown(id='State_List',
                                                          options=[{'label':x,'value':x} for x in States.State.unique()],
                                                          value='Karnataka',
                                                          multi=False,
                                                          clearable=False),
                                             className='three columns',style=Web_Layout_Style),
                                         className='row',style=Web_Layout_Style),
                                     html.Div([
                                         html.Div([
                                             dcc.Graph(id='State_Wise_Trendline')
                                         ],className='six columns',style=Web_Layout_Style),
                                         html.Div([
                                             dcc.Graph(id='State_Wise_New_Case')
                                         ],className='six columns',style=Web_Layout_Style)
                                     ],className='row',style=Web_Layout_Style)
                                 ],className='row',style=Web_Layout_Style),
                                 html.Div(
                                     html.H6('TOP 10 STATES WITH HIGHEST ACTIVE CASES',
                                             style=Heading),className='row',style=Web_Layout_Style),
                                 html.Div([
                                     dcc.Graph(id='India_Top_10_States')
                                 ],className='row',style=Web_Layout_Style)
                             ]),
                        dcc.Tab(id='India_Vaccine',
                             label='VACCINATION',
                             value='Tab2-2',
                             style=Tab_Style,
                             selected_style=Tab_Selected_Style,
                             className='custom-tab',
                             selected_className='custom-tab--selected',
                             children=[html.Div([
                                     html.Div([
                                         html.Div(html.H6('INDIA VACCINE STATS',style=Heading),className='row'),
                                         html.Div([
                                             html.Div([
                                                 dash_table.DataTable(id='Vaccine_IndiaCount',
                                                                      columns=[{'name': 'Last Refreshed', 'id': 'Last Refreshed'}, 
                                                                               {'name': Vaccine_Last_Refreshed_India, 'id':Vaccine_Last_Refreshed_India}],
                                                                      data=Vaccine_India_Count.to_dict('records'),
                                                                      style_table={'overflowY': 'auto'},
                                                                      style_header=Data_Table_Header_Style,
                                                                      style_cell=Data_Table_Cell_Style,
                                                                      style_cell_conditional=[{'if':
                                                                                               {'column_id':'Last Refreshed'},
                                                                                               'textAlign':'left'},
                                                                                              {'if':
                                                                                               {'column_id':Vaccine_Last_Refreshed_India},
                                                                                               'textAlign':'right'}])
                                             ],className='six columns',style=Web_Layout_Style),
                                             html.Div([
                                                 html.Br(),
                                                 dcc.Graph(id='Vaccine_India_Count_Plot',
                                                           figure=India_Count_Plot(),
                                                           config = {'displayModeBar': False})
                                             ],className='four columns',style=Web_Layout_Style)
                                         ],className='row',style=Web_Layout_Style),
                                         html.Div(
                                             html.H6('TOP 10 VACCINED STATES',
                                                     style=Heading),
                                             className='row',style=Web_Layout_Style),
                                         html.Div(
                                             dash_table.DataTable(id='Vaccine_IndiaTop10',
                                                                  columns=[{'name': i, 'id': i} for i in Vaccine_IndiaTop10.columns],
                                                                  data=Vaccine_IndiaTop10.to_dict('records'),
                                                                  style_table={'overflowY': 'auto'},
                                                                  sort_action='native',
                                                                  sort_mode='multi',
                                                                  style_header=Data_Table_Header_Style,
                                                                  style_cell=Data_Table_Cell_Style,
                                                                  style_cell_conditional=[{'if':
                                                                                           {'column_id':'State'},
                                                                                           'textAlign':'left'}
                                                                                         ]
                                                                 ),className='row',style=Web_Layout_Style)
                                     ],className='four columns',style=Web_Layout_Style),
                                     html.Div([
                                         html.Div(
                                             html.H6('INDIA VACCINATION',
                                                     style=Heading),className='row',style=Web_Layout_Style),
                                         html.Div(
                                             dcc.Graph(id='Vaccine_India_Plot',
                                                       figure=Vaccine_India_Plot()))
                                     ],className='eight columns',style=Web_Layout_Style)
                                 ],className='row',style=Web_Layout_Style),
                                 html.Div([
                                     html.Div(
                                             dcc.DatePickerRange(
                                                 id='Vaccine_India_Date_Filter',
                                                 min_date_allowed=datetime.datetime(2021,1,1),
                                                 max_date_allowed=datetime.datetime.today().date(),
                                                 initial_visible_month=datetime.datetime.today().date()),
                                             className='three columns',style=Web_Layout_Style),
                                         html.Div(
                                             dcc.Dropdown(id='Vaccine_India_Quick_Date_Filter',
                                                          options=[
                                                              {'label':'Week to Date','value':'Week to Date'},
                                                              {'label':'Previous Week','value':'Previous Week'},
                                                              {'label':'Last 7 Days','value':'Last 7 Days'},
                                                              {'label':'Month to Date','value':'Month to Date'},
                                                              {'label':'Previous Month','value':'Previous Month'},
                                                              {'label':'Last 30 Days','value':'Last 30 Days'},
                                                              {'label':'Year to Date','value':'Year to Date'},
                                                              {'label':'Previous Year','value':'Previous Year'},
                                                              {'label':'All Time','value':'All Time'}],
                                                          value='All Time',
                                                          clearable=False,
                                                          multi=False,
                                                          placeholder='Select Date Range'),
                                             className='two columns',style=Web_Layout_Style),
                                         html.Div(
                                             dcc.Dropdown(id='Vaccine_India_Span',
                                                          options=[
                                                              {'label':'Daily','value':'Date'},
                                                              {'label':'Weekly','value':'Week'},
                                                              {'label':'Monthly','value':'Month'},
                                                              {'label':'Yearly','value':'Year'}],
                                                          value='Date',
                                                          clearable=False,
                                                          multi=False),
                                             className='one columns',style=Web_Layout_Style),
                                     html.Div(
                                         dcc.Dropdown(id='Vaccine_India_Category',
                                                          options=[
                                                              {'label':'18+ Total Doses','value':'18+ Total Doses'},
                                                              {'label':'15-18 Total Doses','value':'15-18 Total Doses'},
                                                              {'label':'12-14 Total Doses','value':'12-14 Total Doses'},
                                                              {'label':'Booster Total Doses','value':'Booster Total Doses'},
                                                              {'label':'Total Doses','value':'Total Doses'}],
                                                          value=['18+ Total Doses'],
                                                          clearable=True,
                                                          multi=True),
                                             className='two columns',style=Web_Layout_Style),
                                     html.Div(
                                         dcc.Dropdown(id='Vaccine_India_Type',
                                                     options=[
                                                         {'label':'Average','value':'Average_'},
                                                         {'label':'7_Day Simple Moving Average','value':'7_Day_Simple_Moving_Average_'},
                                                         {'label':'7_Day Exponential Moving Average','value':'7_Day_Exponential_Moving_Average_'},
                                                         {'label':'Maximum','value':'Maximum_'}],
                                                      value=['Average_','Maximum_'],
                                                      clearable=True,
                                                      multi=True),
                                              className='four columns',style=Web_Layout_Style),
                                     html.Div(
                                             dcc.Dropdown(id='Vaccine_India_Scale',
                                                          options=[
                                                              {'label':'Linear','value':'linear'},
                                                              {'label':'Log','value':'log'}],
                                                          value='linear',
                                                          clearable=False,
                                                          multi=False),
                                             className='one columns',style=Web_Layout_Style),
                                 ],className='row',style=Web_Layout_Style),
                                 html.Div(
                                     html.H6('INDIA VACCINE TRENDLINE',
                                             style=Heading),className='row',style=Web_Layout_Style),
                                 html.Div([
                                     dcc.Graph(id='Vaccine_India_Trendline')
                                 ],className='row',style=Web_Layout_Style),
                                 html.Div([
                                     html.Div(
                                         html.H6('STATE WISE VACCINE TRENDLINE & LATEST CASE COUNT',
                                                 style=Heading),className='row',style=Web_Layout_Style),
                                     html.Div(
                                         html.Div(
                                             dcc.Dropdown(id='Vaccine_State_List',
                                                          options=[{'label':x,'value':x} for x in States.State.unique()],
                                                          value='Karnataka',
                                                          multi=False,
                                                          clearable=False),
                                             className='three columns',style=Web_Layout_Style),
                                         className='row',style=Web_Layout_Style),
                                     html.Div([
                                         html.Div([
                                             dcc.Graph(id='Vaccine_State_Wise_Trendline')
                                         ],className='six columns',style=Web_Layout_Style),
                                         html.Div([
                                             dcc.Graph(id='Vaccine_State_Wise_New_Case')
                                         ],className='six columns',style=Web_Layout_Style)
                                     ],className='row',style=Web_Layout_Style)
                                 ],className='row',style=Web_Layout_Style),
                                 html.Div(
                                     html.H6('TOP 10 STATES WITH HIGHEST VACCINATION',
                                             style=Heading),className='row',style=Web_Layout_Style),
                                 html.Div([
                                     dcc.Graph(id='Vaccine_India_Top_10_States')
                                 ],className='row',style=Web_Layout_Style)
                             ])])])])
                 ])
    ],className='row')
],className='row',style=Web_Layout_Style)                        
                             


# In[302]:


# Seting Date Range

def span_collection(span_type):
    if span_type=='Previous Week':
        start_date=datetime.date.today()-datetime.timedelta(days=datetime.date.today().weekday()+1,weeks=1)
        end_date=start_date+datetime.timedelta(days=6)
    elif span_type=='Week to Date':
        start_date=datetime.date.today()-datetime.timedelta(days=datetime.date.today().weekday()+1)
        end_date=datetime.date.today()
    elif span_type=='Previous Month':
        start_date=datetime.date(datetime.datetime.today().year,datetime.datetime.today().month-1,1)
        end_date=datetime.date(datetime.datetime.today().year,datetime.datetime.today().month-1,
                               calendar.monthrange(datetime.datetime.today().year,datetime.datetime.today().month-1)[1])
    elif span_type=='Month to Date':
        start_date=datetime.date(datetime.datetime.today().year,datetime.datetime.today().month,1)
        end_date=datetime.date.today()
    elif span_type=='Year to Date':
        start_date=datetime.date(datetime.datetime.today().year,1,1)
        end_date=datetime.date.today()
    elif span_type=='Previous Year':
        start_date=datetime.date(datetime.datetime.today().year-1,1,1)
        end_date=datetime.date(datetime.datetime.today().year-1,12,31)
    elif span_type=='All Time':
        start_date=datetime.datetime(2020,6,19)
        end_date=datetime.datetime.today().date()
    elif span_type=='Last 7 Days':
        start_date=datetime.date.today()-datetime.timedelta(days=6)
        end_date=datetime.date.today()
    elif span_type=='Last 30 Days':
        start_date=datetime.date.today()-datetime.timedelta(days=30)
        end_date=datetime.date.today()
    return start_date,end_date
        
@app.callback(
[Output('Global_Date_Filter','start_date'),
Output('Global_Date_Filter','end_date')],
[Input('Global_Quick_Date_Filter','value')])

def Update_Global_Date_Filter(value):
    start_date=span_collection(value)[0]
    end_date=span_collection(value)[1]
    return start_date,end_date

@app.callback(
[Output('India_Date_Filter','start_date'),
Output('India_Date_Filter','end_date')],
[Input('India_Quick_Date_Filter','value')])

def Update_India_Date_Filter(value):
    start_date=span_collection(value)[0]
    end_date=span_collection(value)[1]
    return start_date,end_date

@app.callback(
[Output('Vaccine_India_Date_Filter','start_date'),
Output('Vaccine_India_Date_Filter','end_date')],
[Input('Vaccine_India_Quick_Date_Filter','value')])

def Update_Vaccine_India_Date_Filter(value):
    start_date=span_collection(value)[0]
    end_date=span_collection(value)[1]
    return start_date,end_date


# In[303]:


# Global Trendline

@app.callback(
Output('Global_Trendline','figure'),
[Input('Global_Date_Filter','start_date'),
Input('Global_Date_Filter','end_date'),
Input('Global_Span','value'),
Input('Global_Category','value'),
Input('Global_Type','value'),
Input('Global_Scale','value')])
def Update_Global_Trendline(Start_Date,End_Date,Span_Selected,Category_Selected,Type_Selected,Scale):
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    group=Day_Wise_Global.loc[(Day_Wise_Global.Date>=Start_Date) & (Day_Wise_Global.Date<=End_Date)]
    
    if group.empty==False:
        group=group.groupby([Span_Selected]).sum().reset_index()[[Span_Selected,'Active','Recovered','Deaths','Total Vaccinations']]
        group['7_Day_Simple_Moving_Average_Active']=round(group['Active'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_Recovered']=round(group['Recovered'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_Deaths']=round(group['Deaths'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_Total Vaccinations']=round(group['Total Vaccinations'].rolling(7,min_periods=1).mean(),0)
        group['Average_Active']=round(group['Active'].mean(),0)
        group['Average_Recovered']=round(group['Recovered'].mean(),0)
        group['Average_Deaths']=round(group['Deaths'].mean(),0)
        group['Average_Total Vaccinations']=round(group['Total Vaccinations'].mean(),0)
        group['Maximum_Active']=round(group['Active'].max(),0)
        group['Maximum_Recovered']=round(group['Recovered'].max(),0)
        group['Maximum_Deaths']=round(group['Deaths'].max(),0)
        group['Maximum_Total Vaccinations']=round(group['Total Vaccinations'].max(),0)
        group['7_Day_Exponential_Moving_Average_Active']=round(group['Active'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_Recovered']=round(group['Recovered'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_Deaths']=round(group['Deaths'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_Total Vaccinations']=round(group['Total Vaccinations'].ewm(7,min_periods=1).mean(),0)
        
        if Span_Selected =='Month':
            group['index']=pd.to_datetime(group['Month'])
            group.sort_values('index',ignore_index=True,inplace=True)
        if len(Category_Selected) !=0: 
            fig=go.Figure()
            for i in Category_Selected:
                fig.add_trace(go.Scatter(x=group[Span_Selected],y=group[i],name=i,marker_color=Plot_Colors1[i]))
                if len(Type_Selected)!=0:
                    for j in Type_Selected:
                        fig.add_trace(go.Scatter(x=group[Span_Selected],y=group[j+i],name=j+i,hoverinfo='skip',
                                                 marker_color=Plot_Colors2[j+i],mode='lines',showlegend=True))
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font,type=Scale)
            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
        else:
            fig=go.Figure([go.Scatter(x=group[Span_Selected],y=group['Active'],name='Active',marker_color='yellow'),
                          go.Scatter(x=group[Span_Selected],y=group['Recovered'],name='Recovered',marker_color='green'),
                          go.Scatter(x=group[Span_Selected],y=group['Deaths'],name='Deaths',marker_color='red'),
                          go.Scatter(x=group[Span_Selected],y=group['Total Vaccinations'],name='Total Vaccinations',marker_color='orange')])
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font,
                            tickmode='array' if (group.columns[0]=='Date') and ((End_Date-Start_Date).days>7) else 'linear')
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)

            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
    else:
        fig=No_Data_Available()
    
    return fig


# In[304]:


# Country Trendline

@app.callback(
Output('Country_Wise_Trendline','figure'),
[Input('Global_Date_Filter','start_date'),
Input('Global_Date_Filter','end_date'),
Input('Global_Span','value'),
Input('Global_Category','value'),
Input('Global_Type','value'),
Input('Country_List','value'),
Input('Global_Scale','value')])

def Update_Country_Wise_Trendline(Start_Date,End_Date,Span_Selected,Category_Selected,Type_Selected,Country_Selected,Scale):
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    group=Day_Wise.loc[(Day_Wise.Date>=Start_Date) & (Day_Wise.Date<=End_Date) &
                             (Day_Wise.Country==Country_Selected)]
    
    if group.empty==False:
        group=group.groupby([Span_Selected]).sum().reset_index()[[Span_Selected,'Active','Recovered','Deaths','Total Vaccinations']]
        group['7_Day_Simple_Moving_Average_Active']=round(group['Active'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_Recovered']=round(group['Recovered'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_Deaths']=round(group['Deaths'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_Total Vaccinations']=round(group['Total Vaccinations'].rolling(7,min_periods=1).mean(),0)
        group['Average_Active']=round(group['Active'].mean(),0)
        group['Average_Recovered']=round(group['Recovered'].mean(),0)
        group['Average_Deaths']=round(group['Deaths'].mean(),0)
        group['Average_Total Vaccinations']=round(group['Total Vaccinations'].mean(),0)
        group['Maximum_Active']=round(group['Active'].max(),0)
        group['Maximum_Recovered']=round(group['Recovered'].max(),0)
        group['Maximum_Deaths']=round(group['Deaths'].max(),0)
        group['Maximum_Total Vaccinations']=round(group['Total Vaccinations'].max(),0)
        group['7_Day_Exponential_Moving_Average_Active']=round(group['Active'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_Recovered']=round(group['Recovered'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_Deaths']=round(group['Deaths'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_Total Vaccinations']=round(group['Total Vaccinations'].ewm(7,min_periods=1).mean(),0)
        
        if Span_Selected =='Month':
            group['index']=pd.to_datetime(group['Month'])
            group.sort_values('index',ignore_index=True,inplace=True)
        if len(Category_Selected) !=0: 
            fig=go.Figure()
            for i in Category_Selected:
                fig.add_trace(go.Scatter(x=group[Span_Selected],y=group[i],name=i,marker_color=Plot_Colors1[i]))
                if len(Type_Selected)!=0:
                    for j in Type_Selected:
                        fig.add_trace(go.Scatter(x=group[Span_Selected],y=group[j+i],name=j+i,hoverinfo='skip',
                                                 marker_color=Plot_Colors2[j+i],mode='lines',showlegend=True))
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font,type=Scale)
            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
        else:
            fig=go.Figure([go.Scatter(x=group[Span_Selected],y=group['Active'],name='Active',marker_color='yellow'),
                          go.Scatter(x=group[Span_Selected],y=group['Recovered'],name='Recovered',marker_color='green'),
                          go.Scatter(x=group[Span_Selected],y=group['Deaths'],name='Deaths',marker_color='red'),
                          go.Scatter(x=group[Span_Selected],y=group['Total Vaccinations'],name='Total Vaccinations',marker_color='orange')])
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font,
                            tickmode='array' if (group.columns[0]=='Date') and ((End_Date-Start_Date).days>7) else 'linear')
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font,type=Scale)

            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
    else:
        fig=No_Data_Available()
    
    return fig


# In[305]:


# New Cases - Country

@app.callback(
Output('Country_Wise_New_Case','figure'),
[Input('Global_Date_Filter','start_date'),
Input('Global_Date_Filter','end_date'),
Input('Global_Span','value'),
Input('Country_List','value')])

def Update_Country_Wise_New_Case(Start_Date,End_Date,Span_Selected,Country_Selected):
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    group=Day_Wise.loc[(Day_Wise.Date>=Start_Date) & (Day_Wise.Date<=End_Date) &
                             (Day_Wise.Country==Country_Selected)]
    if group.empty==False:
        Latest=(group[['Date','Country','Code','Confirmed','Recovered','Deaths']].loc[group.Date==group['Date'].max()]).drop(labels=['Date'],axis=1)
        Old=(group[['Date','Country','Code','Confirmed','Recovered','Deaths']].loc[group.Date==group['Date'].max()-datetime.timedelta(days=1)]).drop(labels=['Date'],axis=1)
        New_Cases=Latest.set_index(['Country','Code']).subtract(Old.set_index(['Country','Code'])).reset_index()
        New_Cases['Active']=New_Cases['Confirmed']-New_Cases['Recovered']-New_Cases['Deaths']
        New_Cases.drop(['Code','Confirmed'],axis=1,inplace=True)
        
        if New_Cases.empty==False and New_Cases.sum(axis=1,numeric_only=True)[0]!=0:
            fig=go.Figure([go.Bar(x=['New Case'],y=New_Cases['Active'],name='Active',marker_color='yellow')
                            ,go.Bar(x=['New Recovered'],y=New_Cases['Recovered'],name='Recovered',marker_color='green'),
                            go.Bar(x=['New Deaths'],y=New_Cases['Deaths'],name='Deaths',marker_color='red')])
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,
                               title='CASES RECORDED ON '+group['Date'].max().date().strftime('%d-%m-%Y')+' for '+Country_Selected,
                              title_x=0.5,titlefont=Fig_Title_Font,font=Fig_Font)
        else:
            fig=No_Data_Available()
    else:
        fig=No_Data_Available()
    return fig


# In[306]:


# Top 10 Countries

@app.callback(
Output('Top_10_Countries','figure'),
[Input('Global_Date_Filter','start_date'),
Input('Global_Date_Filter','end_date'),
Input('Global_Span','value')])

def Update_Top_10_Countries(Start_Date,End_Date,Span_Selected):
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    group=Day_Wise.loc[(Day_Wise.Date>=Start_Date) & (Day_Wise.Date<=End_Date)]
    if group.empty==False:
        ddf1=group.loc[group.Recovered!=0]
        ddf1=ddf1.loc[ddf1.groupby(['Country'])['Date'].idxmax(),['Country','Date','Recovered']]
        ddf1['Recovered Modified']=ddf1['Recovered'].astype(str)+' as on (' + ddf1['Date'].dt.strftime('%Y-%m-%d') +')'
        ddf2=group.loc[group['Total Vaccinations']!=0]
        ddf2=ddf2.loc[ddf2.groupby(['Country'])['Date'].idxmax(),['Country','Date','Total Vaccinations']]
        ddf2['Total Vaccinations Modified']=ddf2['Total Vaccinations'].astype(str)+' as on (' + ddf2['Date'].dt.strftime('%Y-%m-%d') +')'

        Global=group.loc[group.Date==group['Date'].max(),['Country','Code','Date','Week','Month', 'Year',
                                                                   'Confirmed', 'Deaths']].reset_index().drop('index',axis=1)
        Global=Global.merge(ddf1[['Country','Recovered','Recovered Modified']],how='left',on='Country').fillna(0)
        Global=Global.merge(ddf2[['Country','Total Vaccinations','Total Vaccinations Modified']],how='left',on='Country').fillna(0)
        Global[['Recovered','Total Vaccinations']]=Global[['Recovered','Total Vaccinations']].astype('int64')

        Top10=Global.sort_values('Confirmed',ascending=False,ignore_index=True)[:10].drop(['Date','Week','Month','Year'],axis=1)

        fig=go.Figure([go.Bar(x=Top10['Country'],y=Top10['Total Vaccinations'],hovertext=Top10['Total Vaccinations Modified'],hovertemplate='<br>%{x}, %{hovertext}',name='Total Vaccinations',legendgroup='Total Vaccinations',marker_color='orange'),
                       go.Bar(x=Top10['Country'],y=Top10['Recovered'],hovertext=Top10['Recovered Modified'],hovertemplate='<br>%{x}, %{hovertext}',name='Recovered',legendgroup='Recovered',marker_color='green'),
                       go.Bar(x=Top10['Country'],y=Top10['Deaths'],name='Deaths',legendgroup='Deaths',marker_color='red')])
        fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
        fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
        fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
    else:
        fig=No_Data_Available()
    return fig


# In[307]:


# India Trendline

@app.callback(
Output('India_Trendline','figure'),
[Input('India_Date_Filter','start_date'),
Input('India_Date_Filter','end_date'),
Input('India_Span','value'),
Input('India_Category','value'),
Input('India_Type','value'),
Input('India_Scale','value')])

def Update_India_Trendline(Start_Date,End_Date,Span_Selected,Category_Selected,Type_Selected,Scale):
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    group=India.loc[(India.Date>=Start_Date) & (India.Date<=End_Date)]
    
    if group.empty==False:
        group=group.groupby([Span_Selected]).sum().reset_index()[[Span_Selected,'Active','Recovered','Deaths']]
        group['7_Day_Simple_Moving_Average_Active']=round(group['Active'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_Recovered']=round(group['Recovered'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_Deaths']=round(group['Deaths'].rolling(7,min_periods=1).mean(),0)
        group['Average_Active']=round(group['Active'].mean(),0)
        group['Average_Recovered']=round(group['Recovered'].mean(),0)
        group['Average_Deaths']=round(group['Deaths'].mean(),0)
        group['Maximum_Active']=round(group['Active'].max(),0)
        group['Maximum_Recovered']=round(group['Recovered'].max(),0)
        group['Maximum_Deaths']=round(group['Deaths'].max(),0)
        group['7_Day_Exponential_Moving_Average_Active']=round(group['Active'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_Recovered']=round(group['Recovered'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_Deaths']=round(group['Deaths'].ewm(7,min_periods=1).mean(),0)
        
        if Span_Selected =='Month':
            group['index']=pd.to_datetime(group['Month'])
            group.sort_values('index',ignore_index=True,inplace=True)
        if len(Category_Selected) !=0: 
            fig=go.Figure()
            for i in Category_Selected:
                fig.add_trace(go.Scatter(x=group[Span_Selected],y=group[i],name=i,marker_color=Plot_Colors1[i]))
                if len(Type_Selected)!=0:
                    for j in Type_Selected:
                        fig.add_trace(go.Scatter(x=group[Span_Selected],y=group[j+i],name=j+i,hoverinfo='skip',
                                                 marker_color=Plot_Colors2[j+i],mode='lines',showlegend=True))
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font,type=Scale)
            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
        else:
            fig=go.Figure([go.Scatter(x=group[Span_Selected],y=group['Active'],name='Active',marker_color='yellow'),
                      go.Scatter(x=group[Span_Selected],y=group['Recovered'],name='Recovered',marker_color='green'),
                      go.Scatter(x=group[Span_Selected],y=group['Deaths'],name='Deaths',marker_color='red')])
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font,
                            tickmode='array' if (group.columns[0]=='Date') and ((End_Date-Start_Date).days>7) else 'linear')
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font,type=Scale)

            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
    else:
        fig=No_Data_Available()
    
    return fig


# In[308]:


# India Vaccine Trendline

@app.callback(
Output('Vaccine_India_Trendline','figure'),
[Input('Vaccine_India_Date_Filter','start_date'),
Input('Vaccine_India_Date_Filter','end_date'),
Input('Vaccine_India_Span','value'),
Input('Vaccine_India_Category','value'),
Input('Vaccine_India_Type','value'),
Input('Vaccine_India_Scale','value')])

def Update_Vaccine_India_Trendline(Start_Date,End_Date,Span_Selected,Category_Selected,Type_Selected,Scale):
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    group=Vaccine_India.loc[(Vaccine_India.Date>=Start_Date) & (Vaccine_India.Date<=End_Date)]
    
    if group.empty==False:
        group=group.groupby([Span_Selected]).sum().reset_index()[[Span_Selected,'18+ Total Doses','15-18 Total Doses','12-14 Total Doses','Booster Total Doses','Total Doses']]
        group['7_Day_Simple_Moving_Average_18+ Total Doses']=round(group['18+ Total Doses'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_15-18 Total Doses']=round(group['15-18 Total Doses'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_12-14 Total Doses']=round(group['12-14 Total Doses'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_Booster Total Doses']=round(group['Booster Total Doses'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_Total Doses']=round(group['Total Doses'].rolling(7,min_periods=1).mean(),0)
        group['Average_18+ Total Doses']=round(group['18+ Total Doses'].mean(),0)
        group['Average_15-18 Total Doses']=round(group['15-18 Total Doses'].mean(),0)
        group['Average_12-14 Total Doses']=round(group['12-14 Total Doses'].mean(),0)
        group['Average_Booster Total Doses']=round(group['Booster Total Doses'].mean(),0)
        group['Average_Total Doses']=round(group['Total Doses'].mean(),0)
        group['Maximum_18+ Total Doses']=round(group['18+ Total Doses'].max(),0)
        group['Maximum_15-18 Total Doses']=round(group['15-18 Total Doses'].max(),0)
        group['Maximum_12-14 Total Doses']=round(group['12-14 Total Doses'].max(),0)
        group['Maximum_Booster Total Doses']=round(group['Booster Total Doses'].max(),0)
        group['Maximum_Total Doses']=round(group['Total Doses'].max(),0)
        group['7_Day_Exponential_Moving_Average_18+ Total Doses']=round(group['18+ Total Doses'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_15-18 Total Doses']=round(group['15-18 Total Doses'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_12-14 Total Doses']=round(group['12-14 Total Doses'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_Booster Total Doses']=round(group['Booster Total Doses'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_Total Doses']=round(group['Total Doses'].ewm(7,min_periods=1).mean(),0)
        
        if Span_Selected =='Month':
            group['index']=pd.to_datetime(group['Month'])
            group.sort_values('index',ignore_index=True,inplace=True)
        if len(Category_Selected) !=0: 
            fig=go.Figure()
            for i in Category_Selected:
                fig.add_trace(go.Scatter(x=group[Span_Selected],y=group[i],name=i,marker_color=Plot_Colors1[i]))
                if len(Type_Selected)!=0:
                    for j in Type_Selected:
                        fig.add_trace(go.Scatter(x=group[Span_Selected],y=group[j+i],name=j+i,hoverinfo='skip',
                                                 marker_color=Plot_Colors2[j+i],mode='lines',showlegend=True))
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font,type=Scale)
            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
        else:
            fig=go.Figure([go.Scatter(x=group[Span_Selected],y=group['18+ Total Doses'],name='18+ Total Doses',marker_color='#007f5f'),
                          go.Scatter(x=group[Span_Selected],y=group['15-18 Total Doses'],name='15-18 Total Doses',marker_color='#2b9348'),
                          go.Scatter(x=group[Span_Selected],y=group['12-14 Total Doses'],name='12-14 Total Doses',marker_color='#55a630'),
                          go.Scatter(x=group[Span_Selected],y=group['Booster Total Doses'],name='BoosterTotal Doses',marker_color='#80b918'),
                          go.Scatter(x=group[Span_Selected],y=group['Total Doses'],name='Total Doses',marker_color='red')])
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font,
                            tickmode='array' if (group.columns[0]=='Date') and ((End_Date-Start_Date).days>7) else 'linear')
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font,type=Scale)

            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
    else:
        fig=No_Data_Available()
    
    return fig


# In[309]:


# State Trendline

@app.callback(
Output('State_Wise_Trendline','figure'),
[Input('India_Date_Filter','start_date'),
Input('India_Date_Filter','end_date'),
Input('India_Span','value'),
Input('India_Category','value'),
Input('India_Type','value'),
Input('State_List','value'),
Input('India_Scale','value')])

def Update_State_Wise_Trendline(Start_Date,End_Date,Span_Selected,Category_Selected,Type_Selected,State_Selected,Scale):
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    group=States.loc[(States.Date>=Start_Date) & (States.Date<=End_Date) & (States.State==State_Selected)]
    
    if group.empty==False:
        group=group.groupby([Span_Selected]).sum().reset_index()[[Span_Selected,'Active','Recovered','Deaths']]
        group['7_Day_Simple_Moving_Average_Active']=round(group['Active'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_Recovered']=round(group['Recovered'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_Deaths']=round(group['Deaths'].rolling(7,min_periods=1).mean(),0)
        group['Average_Active']=round(group['Active'].mean(),0)
        group['Average_Recovered']=round(group['Recovered'].mean(),0)
        group['Average_Deaths']=round(group['Deaths'].mean(),0)
        group['Maximum_Active']=round(group['Active'].max(),0)
        group['Maximum_Recovered']=round(group['Recovered'].max(),0)
        group['Maximum_Deaths']=round(group['Deaths'].max(),0)
        group['7_Day_Exponential_Moving_Average_Active']=round(group['Active'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_Recovered']=round(group['Recovered'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_Deaths']=round(group['Deaths'].ewm(7,min_periods=1).mean(),0)
        
        if Span_Selected =='Month':
            group['index']=pd.to_datetime(group['Month'])
            group.sort_values('index',ignore_index=True,inplace=True)
        if len(Category_Selected) !=0: 
            fig=go.Figure()
            for i in Category_Selected:
                fig.add_trace(go.Scatter(x=group[Span_Selected],y=group[i],name=i,marker_color=Plot_Colors1[i]))
                if len(Type_Selected)!=0:
                    for j in Type_Selected:
                        fig.add_trace(go.Scatter(x=group[Span_Selected],y=group[j+i],name=j+i,hoverinfo='skip',
                                                 marker_color=Plot_Colors2[j+i],mode='lines',showlegend=True))
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font,type=Scale)
            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
        else:
            fig=go.Figure([go.Scatter(x=group[Span_Selected],y=group['Active'],name='Active',marker_color='yellow'),
                      go.Scatter(x=group[Span_Selected],y=group['Recovered'],name='Recovered',marker_color='green'),
                      go.Scatter(x=group[Span_Selected],y=group['Deaths'],name='Deaths',marker_color='red')])
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font,
                            tickmode='array' if (group.columns[0]=='Date') and ((End_Date-Start_Date).days>7) else 'linear')
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)

            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
    else:
        fig=No_Data_Available()
    
    return fig


# In[310]:


# State Vaccine Trendline

@app.callback(
Output('Vaccine_State_Wise_Trendline','figure'),
[Input('Vaccine_India_Date_Filter','start_date'),
Input('Vaccine_India_Date_Filter','end_date'),
Input('Vaccine_India_Span','value'),
Input('Vaccine_India_Category','value'),
Input('Vaccine_India_Type','value'),
Input('Vaccine_State_List','value'),
Input('Vaccine_India_Scale','value')])

def Update_Vaccine_State_Wise_Trendline(Start_Date,End_Date,Span_Selected,Category_Selected,Type_Selected,State_Selected,Scale):
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    group=Vaccine_States.loc[(Vaccine_States.Date>=Start_Date) & (Vaccine_States.Date<=End_Date) & 
                             (Vaccine_States.State==State_Selected)]
    
    if group.empty==False:
        group=group.groupby([Span_Selected]).sum().reset_index()[[Span_Selected,'18+ Total Doses','15-18 Total Doses','12-14 Total Doses','Booster Total Doses','Total Doses']]
        group['7_Day_Simple_Moving_Average_18+ Total Doses']=round(group['18+ Total Doses'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_15-18 Total Doses']=round(group['15-18 Total Doses'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_12-14 Total Doses']=round(group['12-14 Total Doses'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_Booster Total Doses']=round(group['Booster Total Doses'].rolling(7,min_periods=1).mean(),0)
        group['7_Day_Simple_Moving_Average_Total Doses']=round(group['Total Doses'].rolling(7,min_periods=1).mean(),0)
        group['Average_18+ Total Doses']=round(group['18+ Total Doses'].mean(),0)
        group['Average_15-18 Total Doses']=round(group['15-18 Total Doses'].mean(),0)
        group['Average_12-14 Total Doses']=round(group['12-14 Total Doses'].mean(),0)
        group['Average_Booster Total Doses']=round(group['Booster Total Doses'].mean(),0)
        group['Average_Total Doses']=round(group['Total Doses'].mean(),0)
        group['Maximum_18+ Total Doses']=round(group['18+ Total Doses'].max(),0)
        group['Maximum_15-18 Total Doses']=round(group['15-18 Total Doses'].max(),0)
        group['Maximum_12-14 Total Doses']=round(group['12-14 Total Doses'].max(),0)
        group['Maximum_Booster Total Doses']=round(group['Booster Total Doses'].max(),0)
        group['Maximum_Total Doses']=round(group['Total Doses'].max(),0)
        group['7_Day_Exponential_Moving_Average_18+ Total Doses']=round(group['18+ Total Doses'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_15-18 Total Doses']=round(group['15-18 Total Doses'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_12-14 Total Doses']=round(group['12-14 Total Doses'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_Booster Total Doses']=round(group['Booster Total Doses'].ewm(7,min_periods=1).mean(),0)
        group['7_Day_Exponential_Moving_Average_Total Doses']=round(group['Total Doses'].ewm(7,min_periods=1).mean(),0)
        
        if Span_Selected =='Month':
            group['index']=pd.to_datetime(group['Month'])
            group.sort_values('index',ignore_index=True,inplace=True)
        if len(Category_Selected) !=0: 
            fig=go.Figure()
            for i in Category_Selected:
                fig.add_trace(go.Scatter(x=group[Span_Selected],y=group[i],name=i,marker_color=Plot_Colors1[i]))
                if len(Type_Selected)!=0:
                    for j in Type_Selected:
                        fig.add_trace(go.Scatter(x=group[Span_Selected],y=group[j+i],name=j+i,hoverinfo='skip',
                                                 marker_color=Plot_Colors2[j+i],mode='lines',showlegend=True))
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font,type=Scale)
            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
        else:
            fig=go.Figure([go.Scatter(x=group[Span_Selected],y=group['18+ Total Doses'],name='18+ Total Doses',marker_color='#007f5f'),
                          go.Scatter(x=group[Span_Selected],y=group['15-18 Total Doses'],name='15-18 Total Doses',marker_color='#2b9348'),
                          go.Scatter(x=group[Span_Selected],y=group['12-14 Total Doses'],name='12-14 Total Doses',marker_color='#55a630'),
                          go.Scatter(x=group[Span_Selected],y=group['Booster Total Doses'],name='BoosterTotal Doses',marker_color='#80b918'),
                          go.Scatter(x=group[Span_Selected],y=group['Total Doses'],name='Total Doses',marker_color='red')])
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font,
                            tickmode='array' if (group.columns[0]=='Date') and ((End_Date-Start_Date).days>7) else 'linear')
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)

            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
    else:
        fig=No_Data_Available()
    
    return fig


# In[311]:


# New Cases - State

@app.callback(
Output('State_Wise_New_Case','figure'),
[Input('India_Date_Filter','start_date'),
Input('India_Date_Filter','end_date'),
Input('India_Span','value'),
Input('State_List','value')])

def Update_State_Wise_New_Case(Start_Date,End_Date,Span_Selected,State_Selected):
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    group=States.loc[(States.Date>=Start_Date) & (States.Date<=End_Date) &
                             (States.State==State_Selected)]
    if group.empty==False:
        Latest=(group[['Date','State','Confirmed','Recovered','Deaths']].loc[group.Date==group['Date'].max()]).drop(labels=['Date'],axis=1)
        Old=(group[['Date','State','Confirmed','Recovered','Deaths']].loc[group.Date==group['Date'].max()-datetime.timedelta(days=1)]).drop(labels=['Date'],axis=1)
        New_Cases=Latest.set_index(['State']).subtract(Old.set_index(['State'])).reset_index()
        New_Cases['Active']=New_Cases['Confirmed']-New_Cases['Recovered']-New_Cases['Deaths']
        New_Cases.drop(['Confirmed'],axis=1,inplace=True)
        New_Cases['Active']=New_Cases['Active'].apply(lambda x: 0 if x<0 else x)
        
        if New_Cases.empty==False  and New_Cases.sum(axis=1,numeric_only=True)[0]!=0:
            fig=go.Figure([go.Bar(x=['New Case'],y=New_Cases['Active'],name='Active',marker_color='yellow')
                            ,go.Bar(x=['New Recovered'],y=New_Cases['Recovered'],name='Recovered',marker_color='green'),
                            go.Bar(x=['New Deaths'],y=New_Cases['Deaths'],name='Deaths',marker_color='red')])
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,
                               title='CASES RECORDED ON '+group['Date'].max().date().strftime('%d-%m-%Y')+' for '+State_Selected,
                              title_x=0.5,titlefont=Fig_Title_Font,font=Fig_Font)
        else:
            fig=No_Data_Available()
    else:
        fig=No_Data_Available()
    return fig


# In[312]:


# New Vaccine - State

@app.callback(
Output('Vaccine_State_Wise_New_Case','figure'),
[Input('Vaccine_India_Date_Filter','start_date'),
Input('Vaccine_India_Date_Filter','end_date'),
Input('Vaccine_India_Span','value'),
Input('Vaccine_State_List','value')])

def Update_Vaccine_State_Wise_New_Case(Start_Date,End_Date,Span_Selected,State_Selected):
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    group=Vaccine_States.loc[(Vaccine_States.Date>=Start_Date) & (Vaccine_States.Date<=End_Date) &
                             (Vaccine_States.State==State_Selected)]
    if group.empty==False:
        Latest=(group[['Date','State','18+ Total Doses','15-18 Total Doses','12-14 Total Doses','Booster Total Doses','Total Doses']].loc[group.Date==group['Date'].max()]).drop(labels=['Date'],axis=1)
        Old=(group[['Date','State','18+ Total Doses','15-18 Total Doses','12-14 Total Doses','Booster Total Doses','Total Doses']].loc[group.Date==group['Date'].max()-datetime.timedelta(days=1)]).drop(labels=['Date'],axis=1)
        New_Cases=Latest.set_index(['State']).subtract(Old.set_index(['State'])).reset_index()
        if New_Cases.empty==False  and New_Cases.sum(axis=1,numeric_only=True)[0]!=0:
            fig=go.Figure([go.Bar(x=['18+ Total Doses'],y=New_Cases['18+ Total Doses'],name='18+ Total Doses',marker_color='#007f5f'),
                            go.Bar(x=['15-18 Total Doses'],y=New_Cases['15-18 Total Doses'],name='15-18 Total Doses',marker_color='#2b9348'),
                            go.Bar(x=['12-14 Total Doses'],y=New_Cases['12-14 Total Doses'],name='12-14 Total Doses',marker_color='#55a630'),
                              go.Bar(x=['Booster Total Doses'],y=New_Cases['15-18 Total Doses'],name='15-18 Total Doses',marker_color='#80b918')])
            fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
            fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
            fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,
                               title='VACCINES GIVEN ON '+group['Date'].max().date().strftime('%d-%m-%Y')+' for '+State_Selected,
                              title_x=0.5,titlefont=Fig_Title_Font,font=Fig_Font)
        else:
            fig=No_Data_Available()
    else:
        fig=No_Data_Available()
    return fig


# In[313]:


# Top 10 States

@app.callback(
Output('India_Top_10_States','figure'),
[Input('India_Date_Filter','start_date'),
Input('India_Date_Filter','end_date'),
Input('India_Span','value')])

def Update_India_Top_10_States(Start_Date,End_Date,Span_Selected):
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    group=States.loc[(States.Date>=Start_Date) & (States.Date<=End_Date)]
    if group.empty==False:
        IndiaTop10=group.loc[group.Date==group.Date.max()]
        IndiaTop10=IndiaTop10.sort_values('Active',ascending=False,ignore_index=True)[:10]
        Top10=IndiaTop10[['State','Confirmed','Active','Recovered','Deaths']]

        fig=go.Figure([go.Bar(x=Top10['State'],y=Top10['Active'],name='Active',legendgroup='Active',marker_color='yellow'),
                       go.Bar(x=Top10['State'],y=Top10['Recovered'],name='Recovered',legendgroup='Recovered',marker_color='green'),
                       go.Bar(x=Top10['State'],y=Top10['Deaths'],name='Deaths',legendgroup='Deaths',marker_color='red')])
        fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
        fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
        fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
    else:
        fig=No_Data_Available()
    return fig


# In[314]:


# Top 10 States Vaccines

@app.callback(
Output('Vaccine_India_Top_10_States','figure'),
[Input('Vaccine_India_Date_Filter','start_date'),
Input('Vaccine_India_Date_Filter','end_date'),
Input('Vaccine_India_Span','value')])

def Update_Vaccine_India_Top_10_States(Start_Date,End_Date,Span_Selected):
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    group=Vaccine_States.loc[(Vaccine_States.Date>=Start_Date) & (Vaccine_States.Date<=End_Date)]
    if group.empty==False:
        Vaccine_IndiaTop10=group.loc[group.Date==group.Date.max()]
        Vaccine_IndiaTop10=Vaccine_IndiaTop10.sort_values('Total Doses',ascending=False,ignore_index=True)[:10]
        Top10=Vaccine_IndiaTop10[['State','18+ Total Doses','15-18 Total Doses','12-14 Total Doses','Booster Total Doses']]

        fig=go.Figure([go.Bar(x=Top10['State'],y=Top10['18+ Total Doses'],name='18+ Total Doses',legendgroup='18+ Total Doses',marker_color='#007f5f'),
                       go.Bar(x=Top10['State'],y=Top10['15-18 Total Doses'],name='15-18 Total Doses',legendgroup='15-18 Total Doses',marker_color='#2b9348'),
                       go.Bar(x=Top10['State'],y=Top10['12-14 Total Doses'],name='12-14 Total Doses',legendgroup='12-14 Total Doses',marker_color='#55a630'),
                      go.Bar(x=Top10['State'],y=Top10['Booster Total Doses'],name='Booster Total Doses',legendgroup='Booster Total Doses',marker_color='#80b918')])
        fig.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
        fig.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
        fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)
    else:
        fig=No_Data_Available()
    return fig


# In[315]:


if __name__ == '__main__':
    app.run(debug=False)

