import dash
import io
import dash_core_components as dcc
import dash_html_components as html
from flask_caching import Cache
import os
import time
import random
from collections import deque
from dash.dependencies import Input, Output, Event
from pandas_datareader.data import DataReader
import plotly
import plotly.graph_objs as go
import numpy as np
import pandas as pd
import psycopg2
import configparser
from datetime import datetime as dt

app = dash.Dash(__name__)
server = app.server
app.config.suppress_callback_exceptions = True

# Read database credentials
config = configparser.ConfigParser()
config.read("/var/www/Fuel-Fighter-Visualization/psql.conf")

mapbox_access_token = 'pk.eyJ1IjoiY293bGVyIiwiYSI6ImNqZ293dGw1ejQwN2EyeHM3d3o1aGtiYWcifQ.-sdW6CTRqYgSNKGNfK0gpQ'
df = pd.read_csv(
    'https://raw.githubusercontent.com/plotly' +
    '/datasets/master/2011_february_us_airport_traffic.csv')


def ConfigSectionMap(section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

psql_db = ConfigSectionMap("Credentials")['dbname']
psql_user = ConfigSectionMap("Credentials")['user']
psql_pwd = ConfigSectionMap("Credentials")['password']


# Connect to database
try:
    conn = psycopg2.connect(dbname=psql_db, user=psql_user, password=psql_pwd)
except:
    print("I am unable to connect to the database.")

cur = conn.cursor()

max_length = 1000
times = deque(maxlen=max_length)
BMS_State = deque(maxlen=max_length)
BMS_PreChargeTimeout = deque(maxlen=max_length)
BMS_LTC_LossOfSignal = deque(maxlen=max_length)
BMS_OverVoltage = deque(maxlen=max_length)
BMS_UnderVoltage = deque(maxlen=max_length)
BMS_OverCurrent = deque(maxlen=max_length)
BMS_OverTemp = deque(maxlen=max_length)
BMS_NoDataOnStartup = deque(maxlen=max_length)
BMS_Battery_Current = deque(maxlen=max_length)
BMS_Battery_Voltage = deque(maxlen=max_length)

data_dict_graphs = {
        "BMS Battery Current": BMS_Battery_Current, # int
        "BMS Battery Voltage": BMS_Battery_Voltage # int
        }

data_dict = {
        "BMS State": BMS_State, # (0/1/2/3)
        "BMS_PreChargeTimeout": BMS_PreChargeTimeout, # Boolean
        "BMS_LTC_LossOfSignal": BMS_LTC_LossOfSignal,# Boolean
        "BMS_OverVoltage": BMS_OverVoltage,# Boolean
        "BMS_UnderVoltage": BMS_UnderVoltage,# Boolean
        "BMS_OverCurrent": BMS_OverCurrent,# Boolean
        "BMS_OverTemp": BMS_OverTemp,# Boolean
        "BMS_NoDataOnStartup": BMS_NoDataOnStartup,# Boolean
        "BMS Battery Current": BMS_Battery_Current, # int
        "BMS Battery Voltage": BMS_Battery_Voltage # int
        }

status_data = ['BMS_PreChargeTimeout', 'BMS_LTC_LossOfSignal', 'BMS_OverVoltage', 'BMS_UnderVoltage', 'BMS_OverCurrent', 'BMS_OverTemp', 'BMS_NoDataOnStartup']

def append_data(n):
    if(times.count(n[0]) == 0):
        times.append(n[0])
        BMS_State.append(n[1])
        # Error flags
        BMS_PreChargeTimeout.append(n[2])
        BMS_LTC_LossOfSignal.append(n[3])
        BMS_OverVoltage.append(n[4])
        BMS_UnderVoltage.append(n[5])
        BMS_OverCurrent.append(n[6])
        BMS_OverTemp.append(n[7])
        BMS_NoDataOnStartup.append(n[8])
        # BMS Battery
        BMS_Battery_Current.append(n[9])
        BMS_Battery_Voltage.append(n[10])


def update_obd_values(times, BMS_State, BMS_PreChargeTimeout, BMS_LTC_LossOfSignal, BMS_OverVoltage, BMS_UnderVoltage, BMS_OverCurrent, BMS_OverTemp, BMS_NoDataOnStartup, BMS_Battery_Current, BMS_Battery_Voltage):
    cur.execute("SELECT * FROM sensors ORDER BY times desc limit 50;")
    n = cur.fetchall()
    old_time = -1
    if times:
        old_time = times.pop()
        times.append(old_time)
        if(str(n[0][0]) != str(old_time)):
            append_data(n[0])
            #append_last_data(n[0])

    else:
        #append_last_data(n[0])
        for i in range(len(n)-1, 0, -1):
            append_data(n[i])


    return times, BMS_State, BMS_PreChargeTimeout, BMS_LTC_LossOfSignal, BMS_OverVoltage, BMS_UnderVoltage, BMS_OverCurrent, BMS_OverTemp, BMS_NoDataOnStartup, BMS_Battery_Current, BMS_Battery_Voltage
times, BMS_State, BMS_PreChargeTimeout, BMS_LTC_LossOfSignal, BMS_OverVoltage, BMS_UnderVoltage, BMS_OverCurrent, BMS_OverTemp, BMS_NoDataOnStartup, BMS_Battery_Current, BMS_Battery_Voltage =  update_obd_values(times, BMS_State, BMS_PreChargeTimeout, BMS_LTC_LossOfSignal, BMS_OverVoltage, BMS_UnderVoltage, BMS_OverCurrent, BMS_OverTemp, BMS_NoDataOnStartup, BMS_Battery_Current, BMS_Battery_Voltage)

app.layout = html.Div([
    html.Div([
        html.H1('DNV GL Fuel Fighter Vehicle Data',
            style={'float': 'middle','color': '#0000FF'
                       }),
        ]),

   dcc.Dropdown(id='vehicle-data-name', options=[{'label': s, 'value': s} for s in data_dict_graphs.keys()],
                 multi=True,
                 clearable=False,
                 placeholder="Select a component"
                 ),

    html.Div(children=html.Div(id='graphs'), className='row'),
    #dcc.Graph(id='live-update-graph-bar'),
    html.Div(children=html.Div(id='live-update-text'), className='row'),
    html.Div(id='live-update-text'),
    html.Div(
        className="nine columns",
        children=dcc.Graph(
            id='graph_map',
            figure={
                'data': [{
                    'lat': [63.416479], 'lon': [10.410054], 'type': 'scattermapbox', 'mode':'markers', 'text':['Fuel fighter car'] 
                }],
                'layout': {
                    'mapbox': {
                        'accesstoken': (
                            'pk.eyJ1IjoiY293bGVyIiwiYSI6ImNqZ293dGw1ejQwN2EyeHM3d3o1aGtiYWcifQ.-sdW6CTRqYgSNKGNfK0gpQ'
                        )
                    },
                    'margin': {
                        'l': 10, 'r': 10, 'b': 10, 't': 0
                    },
                    'center': {'lat':63.416479, 'lon':10.410054},
                    'autosize': True,
                    'zoom': 7
                }
            }
        )
    ),
    dcc.Interval(id='graph-update',interval=1000),
    html.Div(children=html.Div(id='info'), className='rows'),
    ], className="container",style={'width':'98%','margin-left':10,'margin-right':10,'max-width':50000 })

#NOT READY
# @app.callback(
#     Output('graph_map', 'children'),
#     [Input('graph_map', 'selectedData')])
# def display_data(selectedData):
#     print("TOUCHED \n \n \n")
#     return json.dumps(selectedData, indent=2)

# TEXT
@app.callback(
    dash.dependencies.Output('live-update-text','children'),
    events=[dash.dependencies.Event('graph-update', 'interval')]
    )
def update_metrics():
    last_BMS_battery_voltage = BMS_Battery_Voltage.pop()
    BMS_Battery_Voltage.append(last_BMS_battery_voltage)
    last_BMS_battery_current = BMS_Battery_Current.pop()
    BMS_Battery_Current.append(last_BMS_battery_current)
    last_BMS_State = BMS_State.pop()
    BMS_State.append(last_BMS_State)
    last_BMS_PreChargeTimeout = BMS_PreChargeTimeout.pop()
    BMS_PreChargeTimeout.append(last_BMS_PreChargeTimeout)
    last_BMS_OverVoltage = BMS_OverVoltage.pop()
    BMS_OverVoltage.append(last_BMS_OverVoltage)
    last_BMS_UnderVoltage = BMS_UnderVoltage.pop()
    BMS_UnderVoltage.append(last_BMS_UnderVoltage)
    last_BMS_OverCurrent = BMS_OverCurrent.pop()
    BMS_OverCurrent.append(last_BMS_OverCurrent)
    last_BMS_OverTemp = BMS_OverTemp.pop()
    BMS_OverTemp.append(last_BMS_OverTemp)
    last_BMS_NoDataOnStartup = BMS_NoDataOnStartup.pop()
    BMS_NoDataOnStartup.append(last_BMS_NoDataOnStartup)
    last_BMS_LTC_LossOfSignal = BMS_LTC_LossOfSignal.pop()
    BMS_LTC_LossOfSignal.append(last_BMS_LTC_LossOfSignal)

    lon, lat, alt = 1000, 10000, 100000
    style = {'padding': '5px', 'fontSize': '16px'}
    class_choice = 'col s12'
    Title = 'This is a livestream of different datapoints read from the fuelfighter car sensors. '
    Title_status = 'Important status updates'

    BMS_voltage_div = 'Battery voltage: ' + str(last_BMS_battery_voltage)
    BMS_current_div = 'Battery current: ' + str(last_BMS_battery_current)
    BMS_state_div = 'BMS state: ' + str(last_BMS_State)
    BMS_PreChargeTimeout_div = 'BMS PreChargeTimeout: ' + str(last_BMS_PreChargeTimeout)
    BMS_OverVoltage_div = 'BMS OverVoltage: ' + str(last_BMS_OverVoltage)
    BMS_UnderVoltage_div = 'BMS UnderVoltage: ' + str(last_BMS_UnderVoltage)
    BMS_OverCurrent_div = 'BMS OverCurrent: ' + str(last_BMS_OverCurrent)
    BMS_OverTemp_div = 'BMS OverTemp: ' + str(last_BMS_OverTemp)
    BMS_NoDataOnStartup_div = 'BMS NoDataOnStartup: ' + str(last_BMS_NoDataOnStartup)
    BMS_LTC_LossOfSignal_div = 'BMS LTC_LossOfSignal: ' + str(last_BMS_LTC_LossOfSignal)
    output = (
        html.Div([html.Div(Title, style={'color': 'blue', 'fontSize': 30}),
                  html.Div(BMS_voltage_div, style={'fontSize': 14}),
                  html.Div(BMS_current_div, style={'fontSize': 14}),
                  html.Div(Title_status, style={'color': 'blue', 'fontSize': 30}),
                  html.Div([
                      html.Div(BMS_state_div),
                      html.Div(BMS_PreChargeTimeout_div),
                      html.Div(BMS_OverVoltage_div),
                      html.Div(BMS_UnderVoltage_div),
                      html.Div(BMS_OverCurrent_div),
                      html.Div(BMS_OverTemp_div),
                      html.Div(BMS_NoDataOnStartup_div),
                      html.Div(BMS_LTC_LossOfSignal_div)
                      ], style={'fontSize': 14})
                      ]))
    return output

# SCATTER
@app.callback(
    dash.dependencies.Output('graphs','children'),
    [dash.dependencies.Input('vehicle-data-name', 'value')],
    events=[dash.dependencies.Event('graph-update', 'interval')]
    )
def update_graph(data_names):
    graphs = []
    update_obd_values(times, BMS_State, BMS_PreChargeTimeout, BMS_LTC_LossOfSignal, BMS_OverVoltage, BMS_UnderVoltage, BMS_OverCurrent, BMS_OverTemp, BMS_NoDataOnStartup, BMS_Battery_Current, BMS_Battery_Voltage)
    if data_names:
        # if len(data_names)>2:
        #     class_choice = 'col s12 m6 l4'
        # elif len(data_names) == 2:
        #     class_choice = 'col s12 m6 l6'
        #else:
        class_choice = 'col s12'

        status_dict = []

        for data_name in data_names:
            if(data_name in status_data): # We won't display status updates as graphs
                old_data = data_dict[data_name].pop()
                data_dict[data_name].append(old_data)

                # data = go.Bar(
                #     x=list(data_name),
                #     y=list([old_data])
                # )
                # graphs.append(html.Div(dcc.Graph(
                #     id=data_name,
                #     figure={'data': [data],'layout' : go.Layout(title='{}'.format(data_name))}
                # ), className=class_choice))
            else:
                data = go.Scatter(
                    x=list(times),
                    y=list(data_dict[data_name]),
                    name='Scatter',
                    fill="tozeroy",
                    fillcolor="#6897bb"
                )
                graphs.append(html.Div(dcc.Graph(
                    id=data_name,
                    animate=True,
                    figure={'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(times),max(times)]),
                                                                yaxis=dict(range=[0,max(data_dict[data_name])*1.1]),
                                                                title='{}'.format(data_name))}
                ), className=class_choice))

    return graphs
# external_css = ["https://fonts.googleapis.com/css?family=Product+Sans:400,400i,700,700i",
#                 "https://cdn.rawgit.com/plotly/dash-app-stylesheets/2cc54b8c03f4126569a3440aae611bbef1d7a5dd/stylesheet.css"]


# for css in external_css:
#     app.css.append_css({"external_url": css})


# if 'DYNO' in os.environ:
#     app.scripts.append_script({
#         'external_url': 'https://cdn.rawgit.com/chriddyp/ca0d8f02a1659981a0ea7f013a378bbd/raw/e79f3f789517deec58f41251f7dbb6bee72c44ab/plotly_ga.js'
#     })

external_css = ["https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css"]
for css in external_css:
    app.css.append_css({"external_url": css})

external_js = ['https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js']
for js in external_css:
    app.scripts.append_script({'external_url': js})

if __name__ == '__main__':
    app.run_server(debug=False, threaded=True)
