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
from datetime import datetime as dt


app = dash.Dash(__name__)
server = app.server

# Caching for better performance
cache = Cache(server, config={
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', '')
    })
app.config.suppress_callback_exceptions = True

max_length = 100
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
    df = pd.read_csv('sample.csv')
    # if len(times) == 1:
        # createCSV.createCSV()

    times.append(int(df.Time))
    BMS_State.append(int(df.BMS_State))

    # Error flags
    BMS_PreChargeTimeout.append((df.BMS_PreChargeTimeout).bool())
    BMS_LTC_LossOfSignal.append((df.BMS_LTC_LossOfSignal).bool())
    BMS_OverVoltage.append((df.BMS_OverVoltage).bool())
    BMS_UnderVoltage.append((df.BMS_UnderVoltage).bool())
    BMS_OverCurrent.append((df.BMS_OverCurrent).bool())
    BMS_OverTemp.append((df.BMS_OverTemp).bool())
    BMS_NoDataOnStartup.append((df.BMS_NoDataOnStartup).bool())

    # Battery
    BMS_Battery_Current.append(int(df.BMS_Battery_Current))
    BMS_Battery_Voltage.append(int(df.BMS_Battery_Voltage))
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
        interval=5000),
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
    app.run_server()
