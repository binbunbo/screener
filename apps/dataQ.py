#!/usr/bin/env python
# coding: utf-8
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import urllib
from dash_table.Format import Format, Group, Symbol, Scheme, Prefix

import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from app import app
from app import server

idx = pd.IndexSlice

# statsY = pd.read_pickle("F:/DataStock/VND/Raw/statsY_VND")
statsQ = pd.read_pickle('F:/DataStock/VND/Raw/statsQ_VND')

statsQ['dates'] = pd.PeriodIndex(year=statsQ.reset_index()["year"], quarter=statsQ.reset_index()["quarter"])
statsQ['dates'] = statsQ['dates'].dt.to_timestamp(freq='Q')

col = ['ticker', 'year', 'quarter', 'mc', 'rev', 'gp', 'core_e', 'net_income', 'ni_parent', 'ta', 'te', 'tl','debt']

layout = html.Div(children=[
    html.Header(children='Data Quý', className='ml-4',
                style={'font-size': '30px', 'font-weight': 'bold', 'font-family': 'Arial', 'text-align': 'center'}),
    html.Div(children='''Chọn mã CK và nhấn Enter:''', className='ml-4', style={'font-size': '20px'}),
    dcc.Input(id='input', value='VNM', type='text', debounce=True, className='ml-4'),
    html.A(
        'Download Data',
        id='download-link',
        download="rawdata.csv",
        href="",
        target="_blank",
        className='ml-4'
    ),

    html.Div([dash_table.DataTable(
        id='data-output',
        columns=[{"name": i, "id": i, "deletable": False, "selectable": True, 'type': 'numeric',
                  # 'format': Format(groups=3,group=Group.yes)

                  } for i in col],
        editable=True,
        filter_action="native",
        sort_action="native",
        style_cell={'textAlign': 'right', 'font_size': '16px', 'font_family': 'arial','width':'auto'},
        style_cell_conditional=[{'if': {'column_id': c}, 'textAlign': 'left'} for c in ['ticker', 'year', 'quarter']],
        style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}],
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
        fixed_columns={'headers': True, 'data': 3},
        style_table={'minWidth': '100%','overflowX':'auto'}

    )
    ])

])


@app.callback(
    Output(component_id='download-link', component_property='href'),
    [Input(component_id='input', component_property='value')]
)
def update_download_link(ticker):
    ticker = ticker.upper()
    df_string = statsQ.loc[[ticker], col[3:]].to_csv(index=True, encoding='utf-8')
    df_string = "data:text/csv;charset=utf-8,%EF%BB%BF" + urllib.parse.quote(df_string)
    return df_string


@app.callback(
    Output(component_id='data-output', component_property='data'),
    [Input(component_id='input', component_property='value')]
)
def update_table(ticker):
    ticker = ticker.upper()
    pd.options.display.float_format = '{:,.2f}'.format
    df = statsQ.loc[[ticker], col[3:]].reset_index().to_dict('records')
    return df
