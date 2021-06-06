import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
from datetime import datetime
import dash_table
import urllib

import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from app import app
from app import server

idx = pd.IndexSlice
df = pd.read_pickle('F:/DataStock/VND/price_week')
df = df[df['mc'] != 0]

layout = html.Div(children=[
    html.Header(children='Chart giá', className='ml-4',
                style={'font-size': '30px', 'font-weight': 'bold', 'font-family': 'Arial', 'text-align': 'center'}),
    html.Div(children='''Chọn mã CK và nhấn Enter:''', className='ml-4', style={'font-size': '20px'}),
    dcc.Input(id='input', value='VNM', type='text', debounce=True, className='ml-4'),
    html.Div([dcc.Graph(id='price-chart')])
]
)


@app.callback(
    Output(component_id='price-chart', component_property='figure'),
    [Input(component_id='input', component_property='value')]
)
def update_table(ticker):
    ticker = ticker.upper()
    df1 = df.loc[ticker, ['dates', 'open', 'high', 'low', 'close','v']]


    rangeselector = dict(
        visible=True,
        x=0, y=0.9,
        bgcolor='rgba(150, 200, 250, 0.4)',
        font=dict(size=13),
        buttons=list([
            dict(count=1,
                 label='reset',
                 step='all'),
            dict(count=1,
                 label='1yr',
                 step='year',
                 stepmode='backward'),
            dict(count=3,
                 label='3 mo',
                 step='month',
                 stepmode='backward'),
            dict(count=1,
                 label='1 mo',
                 step='month',
                 stepmode='backward'),
            dict(step='all')
        ]))

    colors = []
    for i in range(len(df1['close'])):
        if i != 0:
            if df1['close'][i] > df1['close'][i - 1]:
                colors.append('green')
            else:
                colors.append('red')
        else:
            colors.append('red')

    vol = dict(x=df1['dates'], y=df1['v'],
                         marker=dict(color=colors),
                         type='bar', yaxis='y2', name='Volume')


    data_set = [go.Candlestick(x=df1['dates'],
                               open=df1['open'],
                               high=df1['high'],
                               low=df1['low'],
                               close=df1['close'],
                               increasing_line_color='green',
                               decreasing_line_color='red'
                               ),go.Bar(vol)]
    return {'data': data_set,
            'layout': go.Layout(title='Biểu đồ giá ' + str(ticker),
                                xaxis=dict(rangeselector=rangeselector),
                                xaxis_rangeslider_visible=False,
                                yaxis2=go.layout.YAxis(overlaying='y',side='right' ),
                                height=600
                                )}
