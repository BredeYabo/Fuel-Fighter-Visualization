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
import plotly.graph_objs as go
import numpy as np
import pandas as pd
import psycopg2
from datetime import datetime as dt


app = dash.Dash(__name__)
server = app.server

# Start receiving messages
os.system("python3 mqtt.py")


# Caching for better performance
cache = Cache(server, config={
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', '')
    })
app.config.suppress_callback_exceptions = True

# Read database credentials
config = configparser.ConfigParser()
config.read("psql.conf")

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

data_dict = {
        "BMS State": BMS_State, # (0/1/2/3)
        "BMS_PreChargeTimeout": BMS_PreChargeTimeout, # Boolean
        "BMS_LTC_LossOfSignal": BMS_LTC_LossOfSignal,# Boolean
        "BMS_OverVoltage": BMS_OverVoltage,# Boolean
        "BMS_UnderVoltage": BMS_UnderVoltage,# Boolean
        "BMS_OverCurrent": BMS_OverCurrent,# Boolean
        "BMS_OverTemp": BMS_OverTemp,# Boolean
        "BMS_NoDataOnStartup": BMS_NoDataOnStartup,# Boolean
        "BMS_Battery_Current": BMS_Battery_Current, # int
        "BMS_Battery_Voltage": BMS_Battery_Voltage # int
        }

def update_obd_values(times, BMS_State, BMS_PreChargeTimeout, BMS_LTC_LossOfSignal, BMS_OverVoltage, BMS_UnderVoltage, BMS_OverCurrent, BMS_OverTemp, BMS_NoDataOnStartup, BMS_Battery_Current, BMS_Battery_Voltage):
    cur.execute("SELECT * FROM sensors ORDER BY times desc limit 1;")
    n = cur.fetchone()

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

    # Battery
    BMS_Battery_Current.append(n[9])
    BMS_Battery_Voltage.append(n[10])
    # else:
    #     for data_of_interest in [speeds, position, rpms, slope, accelerometer]:
            # data_of_interest.append(data_of_interest[-1]+data_of_interest[-1]*random.uniform(-0.0001,0.0001))
    return times, BMS_State, BMS_PreChargeTimeout, BMS_LTC_LossOfSignal, BMS_OverVoltage, BMS_UnderVoltage, BMS_OverCurrent, BMS_OverTemp, BMS_NoDataOnStartup, BMS_Battery_Current, BMS_Battery_Voltage

times, BMS_State, BMS_PreChargeTimeout, BMS_LTC_LossOfSignal, BMS_OverVoltage, BMS_UnderVoltage, BMS_OverCurrent, BMS_OverTemp, BMS_NoDataOnStartup, BMS_Battery_Current, BMS_Battery_Voltage =  update_obd_values(times, BMS_State, BMS_PreChargeTimeout, BMS_LTC_LossOfSignal, BMS_OverVoltage, BMS_UnderVoltage, BMS_OverCurrent, BMS_OverTemp, BMS_NoDataOnStartup, BMS_Battery_Current, BMS_Battery_Voltage)

app.layout = html.Div([
    html.Div([
        html.H2('DNV GL Fuel Fighter Vehicle Data',
            style={'float': 'left','color': '#0000FF'
                       }),
        ]),
    dcc.Dropdown(id='vehicle-data-name',
                 options=[{'label': s, 'value': s}
                          for s in data_dict.keys()],
                 value=['BMS_State','BMS_UnderVoltage'],
                 multi=True
                 ),
    html.Div(children=html.Div(id='graphs'), className='row'),
    dcc.Interval(
        id='graph-update',
        interval=1000),
    ], className="container",style={'width':'98%','margin-left':10,'margin-right':10,'max-width':50000})


@app.callback(
    dash.dependencies.Output('graphs','children'),
    [dash.dependencies.Input('vehicle-data-name', 'value')],
    events=[dash.dependencies.Event('graph-update', 'interval')]
    )
def update_graph(data_names):
    graphs = []
    update_obd_values(times, BMS_State, BMS_PreChargeTimeout, BMS_LTC_LossOfSignal, BMS_OverVoltage, BMS_UnderVoltage, BMS_OverCurrent, BMS_OverTemp, BMS_NoDataOnStartup, BMS_Battery_Current, BMS_Battery_Voltage)
    if len(data_names)>2:
        class_choice = 'col s12 m6 l4'
    elif len(data_names) == 2:
        class_choice = 'col s12 m6 l6'
    else:
        class_choice = 'col s12'

    for data_name in data_names:
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
                                                        yaxis=dict(range=[min(data_dict[data_name]),max(data_dict[data_name])]),
                                                        margin={'l':50,'r':1,'t':45,'b':1},
                                                        title='{}'.format(data_name))}
            ), className=class_choice))

    return graphs
external_css = ["https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css"]
for css in external_css:
    app.css.append_css({"external_url": css})

external_js = ['https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js']
for js in external_css:
    app.scripts.append_script({'external_url': js})

if __name__ == '__main__':
    app.run_server(debug=False, threaded=True)
