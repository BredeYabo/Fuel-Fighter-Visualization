import dash
import dash_core_components as dcc
import dash_html_components as html
import os
from dash.dependencies import Input, Output

app = dash.Dash(__name__)
server = app.server
import numpy as np
import pandas as pd
from datetime import datetime as dt


app.layout = html.Div([
    html.H1('Fuel Fighter'),
    dcc.Dropdown(
        id='dropdown',
        options=[
            {'label': 'Position', 'value': 'Position'},
        ],
        value='Position'
    ),
    dcc.Graph(id='Test')
])

@app.callback(Output('Test', 'figure'), [Input('dropdown', 'value')])
def update_graph(selected_dropdown_value):
    df = pd.read_csv('sample.csv')
    return {
        'data': [{
            'x': df.x,
            't': df.t
        }]
    }

if __name__ == '__main__':
    app.run_server()
