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
import boto3


app = dash.Dash(__name__)
server = app.server

# Caching for better performance
cache = Cache(server, config={
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', '')
    })
app.config.suppress_callback_exceptions = True

## Downloading the CSV file from S3 bucket
# Boto 3
BUCKET_NAME = 'ff-fipy-csv'
KEY = 'sample.csv'

max_length = 50
times = deque(maxlen=max_length)
speeds = deque(maxlen=max_length)
rpms = deque(maxlen=max_length)
position = deque(maxlen=max_length)
slope = deque(maxlen=max_length)
accelerometer = deque(maxlen=max_length)
data_dict = {
        "Speed": speeds,
        "RPM": rpms,
        "GPS": position,
        "Hill slope": slope,
        "Accelerometer": accelerometer
        }

def update_obd_values(times, speeds, rpms, position, slope, accelerometer):
    times.append(time.time())
    if len(times) == 1:
        #starting relevant values
        speeds.append(random.randrange(180,230))
        rpms.append(random.randrange(1000,9500))
        position.append(random.randrange(95,115))
        slope.append(random.randrange(30,140))
        accelerometer.append(random.randrange(10,90))
    else:
        for data_of_interest in [speeds, position, rpms, slope, accelerometer]:
            data_of_interest.append(data_of_interest[-1]+data_of_interest[-1]*random.uniform(-0.0001,0.0001))

    return times, speeds, rpms, position, slope, accelerometer

times, speeds, rpms, position, slope, accelerometer = update_obd_values(times, speeds, rpms, position, slope, accelerometer)

app.layout = html.Div([
    html.Div([
        html.H2('DNV GL Fuel Fighter Vehicle Data',
            style={'float': 'left','color': '#0000FF'
                       }),
        ]),
    dcc.Dropdown(id='vehicle-data-name',
                 options=[{'label': s, 'value': s}
                          for s in data_dict.keys()],
                 value=['Speed','RPM'],
                 multi=True
                 ),
    html.Div(children=html.Div(id='graphs'), className='row'),
    dcc.Interval(
        id='graph-update',
        interval=3000),
    ], className="container",style={'width':'98%','margin-left':10,'margin-right':10,'max-width':50000})


@app.callback(
    dash.dependencies.Output('graphs','children'),
    [dash.dependencies.Input('vehicle-data-name', 'value')],
    events=[dash.dependencies.Event('graph-update', 'interval')]
    )
def update_graph(data_names):
    graphs = []
    update_obd_values(times, speeds, position, rpms, slope, accelerometer)
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



# @app.callback(Output('live-graph', 'figure'), [Input('dropdown', 'value')])
# def update_graph(selected_dropdown_value):
    # df = pd.read_csv('sample.csv')
    # return {
        # 'data': [{
        #     'x': df.x,
            # 't': df.t
         # }]
    # }


s3 = boto3.resource('s3')
# s3_client = boto3.client('s3')

def getCSV():
    s3.Bucket(BUCKET_NAME).download_file(KEY, 'sample.csv')

# Example usage
# pd_read_csv_s3("s3://my_bucket/my_folder/file.csv", skiprows=2)

if __name__ == '__main__':
    app.run_server()
