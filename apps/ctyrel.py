# coding: utf-8


import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from app import app
import json
import pandas as pd
import requests
import numpy as np
idx = pd.IndexSlice
from app import server

df = pd.read_pickle('D:/Data/df_listed_full')
list_cty = pd.read_pickle('D:/Data/list_cty')
list_cty = list_cty.dropna()['Ticker'].unique()
col1 = ['gp', 'op', 'op1', 'EBT', 'pretax_inc', 'net_income', 'ni_parent', 'core_e']
col3 = ['rev', 'gp', 'op', 'EBT', 'pretax_inc', 'net_income', 'ni_parent', 'core_e']

def margin_func(x, i):
    x[i + "m"] = x[i] / x['rev']

def add_ratios(x):
    x['jv_income'] = x['jv_inc1'] + x['jv_inc2']
    x['cip'] = x['cip1']
    x['tax_rate'] = 1 - x['net_income'] / x['pretax_inc']
    x['op'] = x['gp'] - np.abs(x['admin_exp']) - np.abs(x['sel_exp'])
    x['op1'] = x['op'] + x['jv_income']
    x['EBT'] = x['op'] - np.abs(x['int_exp'])
    x['fin_income'] = x['fin_rev'] - (np.abs(x['fin_exp']) - np.abs(x['int_exp']))
    x['other_income'] = x['other_inc']
    x['bs_gross_fa'] = x['gross_tfa'] + x['gross_ifa'] + x['gross_lease'] + x['gross_ip']
    x['bs_fa'] = x['net_tfa'] + x['net_ifa'] + x['net_ip'] + x['net_lease']
    x['bs_cash'] = (x['cce'] + x['net_st_inv'])
    x['bs_capex'] = -(x.sort_index(level=[0, 1]).groupby(level=0)["bs_fa"].diff(periods=1) +
                      x.sort_index(level=[0, 1]).groupby(level=0)["cip"].diff(periods=1))
    x['bs_ar'] = x['st_ar']
    x['bs_ap'] = x['st_trade_ap']
    x['bs_cust_pre'] = x['st_prepaid_cust'] + x['lt_prepaid_cust'] + x['st_unrev'] + x['lt_unrev']
    x['debt'] = x['st_debt'] + x['lt_debt']
    x['core_e'] = x['op'] * (1 - x['tax_rate'])
    x['op2'] = x['core_e'] + x['jv_income']
    x['netcash'] = (x['bs_cash'] - x['cl'])
    x['ic'] = x['te'] + x['debt']
    x['other_asset'] = x['ta'] - x['bs_cash'] - x['bs_ar'] - x['net_inven'] - x['bs_fa'] - x['cip']
    x['other_lia'] = x['tl'] - x['debt'] - x['bs_ap'] - x['bs_cust_pre']
    x['other_equity'] = x['te'] - x['re'] - x['cap_e'] - x['bs_treasury']

def ttm(x, i):
    x[i + "_4Q"] = x.groupby(level=[0])[i].apply(lambda x: x.rolling(4, min_periods=4).sum())

def add_stats(x):
    x['tax_rate_4Q'] = 1 - x['net_income_4Q'] / x['pretax_inc_4Q']
    x['roe_4Q'] = x['net_income_4Q'] / x['te'].groupby(level=[0]).apply(lambda x: x.rolling(4, min_periods=4).mean())
    x['roic_4Q'] = x['net_income_4Q'] / x['ic'].groupby(level=[0]).apply(lambda x: x.rolling(4, min_periods=4).mean())
    x['roa_4Q'] = x['net_income_4Q'] / x['ta'].groupby(level=[0]).apply(lambda x: x.rolling(4, min_periods=4).mean())
    x['EBToe_core_4Q'] = x['EBT_4Q'] / x['te'].groupby(level=[0]).apply(lambda x: x.rolling(4, min_periods=4).mean())
    x['roe_core_4Q'] = x['EBToe_core_4Q'] * (1 - x['tax_rate_4Q'])
    x['DE'] = x['debt'] / x['te']
    x['DA'] = x['debt'] / x['ta']
    x['ca/ta'] = x['ca'] / x['ta']

def add_statsY(x):
    x['roe'] = x['net_income'] / x.sort_index(level=[0, 1])['te'].groupby(level=[0]).apply(
        lambda x: x.rolling(2, min_periods=2).mean())
    x['roic'] = x['net_income'] / x.sort_index(level=[0, 1])['ic'].groupby(level=[0]).apply(
        lambda x: x.rolling(2, min_periods=2).mean())
    x['roa'] = x['net_income'] / x.sort_index(level=[0, 1])['ta'].groupby(level=[0]).apply(
        lambda x: x.rolling(2, min_periods=2).mean())
    x['EBToe_core'] = x['EBT'] / x.sort_index(level=[0, 1])['te'].groupby(level=[0]).apply(
        lambda x: x.rolling(2, min_periods=2).mean())
    x['roe_core'] = x['EBToe_core'] * (1 - x['tax_rate'])
    x['DE'] = x['debt'] / x['te']
    x['DA'] = x['debt'] / x['ta']
    x['ca/ta'] = x['ca'] / x['ta']
    x['asset_turn'] = x['rev'] / x.sort_index(level=[0, 1])['ta'].groupby(level=[0]).apply(
        lambda x: x.rolling(2, min_periods=2).mean())
    x['ar_turn'] = x['rev'] / x.sort_index(level=[0, 1])['bs_ar'].groupby(level=[0]).apply(
        lambda x: x.rolling(2, min_periods=2).mean())
    x['ap_turn'] = (x['rev'] - x['gp']) / x.sort_index(level=[0, 1])['bs_ap'].groupby(level=[0]).apply(
        lambda x: x.rolling(2, min_periods=2).mean())
    x['inven_turn'] = (x['rev'] - x['gp']) / x.sort_index(level=[0, 1])['net_inven'].groupby(level=[0]).apply(
        lambda x: x.rolling(2, min_periods=2).mean())

def g_funcY(x, i):
    x["g_" + i] = x.sort_index(level=[0, 1]).groupby(level=[0])[i].diff(periods=1) / np.abs(
        x[i].sort_index(level=[0, 1]).shift(1))

def get_df(ticker):
    try:
        return df.loc[idx[:,ticker,:,[1,2,3,4]],:]
    except:
        print('Có lỗi, xin nhập mã khác')

def get_dfY(ticker):
    try:
        return df.loc[idx[:,ticker,:,[5]],:]
    except:
        print('Có lỗi, xin nhập mã khác')

def add_df(ticker):
    # ticker = ticker.upper()
    x = get_df(ticker)
    add_ratios(x)
    for i in col3:
        ttm(x, i)
    for i in col1:
        margin_func(x, i)
    #     for i in col2:
    #         g_func(x, i)
    add_stats(x)
    return x

def add_dfY(ticker):
    # ticker = ticker.upper()
    x = get_dfY(ticker)
    add_ratios(x)
    for i in col1:
        margin_func(x, i)
    for i in col3:
        g_funcY(x, i)
    add_statsY(x)
    return x

layout = html.Div(children=[
    html.Header(children='So sánh công ty', className='ml-4',
                style={'font-size': '30px', 'font-weight': 'bold', 'font-family': 'Arial', 'text-align': 'center'}),
    html.Div(children='''Chọn mã CK và nhấn Enter:''', className='ml-4', style={'font-size': '20px'}),
    dcc.Dropdown(id='input', options=[{'label':i,'value':i} for i in list_cty],value = 'VNM',
                 clearable=True, multi=True, className='ml-4',
                 style={'width': '50%', 'display': 'inline-block','color':'black'}),
    html.Div(id='intermediate-value-ctyrel', style={'display': 'none'}),
    html.Div([
        html.Div([dcc.Graph(id='rel-graphQ1')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='rel-graphQ2')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='rel-graphQ3')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='rel-graphQ4')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='rel-graphQ5')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='rel-graphQ6')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='rel-graphQ7')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='rel-graphQ8')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row')
])

@app.callback(Output('intermediate-value-ctyrel', 'children'),
              [Input(component_id='input', component_property='value')])
# def clean_data(ticker):
#     statsQ = add_df(ticker)
#     statsQ = statsQ.sort_index(level=[0,1])
#     statsQ = statsQ.reset_index()
#     statsQ['dates'] = pd.PeriodIndex(year=statsQ.reset_index()["year"], quarter=statsQ.reset_index()["quarter"])
#     statsQ['dates'] = statsQ['dates'].dt.to_timestamp(freq='Q')
#     return statsQ.to_json(date_format='iso', orient='split')

def clean_data(ticker):
    statsQ = add_dfY(ticker)
    statsQ = statsQ.reset_index()
    return statsQ.to_json(date_format='iso', orient='split')

@app.callback(
    Output(component_id='rel-graphQ1', component_property='figure'),
    [Input(component_id='intermediate-value-ctyrel', component_property='children')]
)
def profit(dat):
    statsQ = pd.read_json(dat, orient='split')
    statsQ = statsQ.groupby('Ticker')
    data_set = []
    for ticker,group in statsQ:
        trace = go.Scatter(y=group['gpm'], x=group['year'],
                       line=dict(width=2), mode='lines',name=ticker)

        data_set.append(trace)

    fig = go.Figure(data=data_set,layout=dict(title='Tỷ suất LN gộp',
                           # xaxis=dict(tickformat='%Y-%b', showgrid=False),
                           yaxis=go.layout.YAxis( tickformat='.1%'),
                           yaxis2=go.layout.YAxis(tickformat='.1%', gridwidth=2, showgrid=False,
                                                    overlaying='y', side='right'),
                           legend=dict(x=1.1, y=1)
                           ))
    return fig.update_layout( template='plotly_dark',title_x=0.5,
                        plot_bgcolor= 'rgba(0, 0, 0, 0)',
                        paper_bgcolor= 'rgba(0, 0, 0, 0)')
@app.callback(
    Output(component_id='rel-graphQ2', component_property='figure'),
    [Input(component_id='intermediate-value-ctyrel', component_property='children')]
)
def profit(dat):
    statsQ = pd.read_json(dat, orient='split')
    statsQ = statsQ.groupby('Ticker')
    data_set = []
    for ticker, group in statsQ:
        trace = go.Scatter(y=group['roe'], x=group['year'],
                           line=dict(width=2), mode='lines', name=ticker)

        data_set.append(trace)

    fig = go.Figure(data=data_set, layout=dict(title='ROE_4Q',
                                               # xaxis=dict(tickformat='%Y-%b', showgrid=False),
                                               yaxis=go.layout.YAxis(tickformat='.1%'),
                                               yaxis2=go.layout.YAxis(tickformat='.1%', gridwidth=2, showgrid=False,
                                                                      overlaying='y', side='right'),
                                               legend=dict(x=1.1, y=1)
                                               ))
    return fig.update_layout( template='plotly_dark',title_x=0.5,
                        plot_bgcolor= 'rgba(0, 0, 0, 0)',
                        paper_bgcolor= 'rgba(0, 0, 0, 0)')
#
# @app.callback(
#     Output(component_id='output-graph2SQLQ', component_property='figure'),
#     [Input(component_id='intermediate-valueSQLQ', component_property='children')]
# )
# def roae(dat):
#     statsQ = pd.read_json(dat, orient='split')
#
#     test1 = go.Scatter(y=statsQ.loc[:, 'roe_4Q'], x=statsQ.loc[:, 'dates'], name="roe", yaxis='y2',
#                        line=dict(color='red', width=3), mode='lines+markers')
#     test2 = go.Scatter(y=statsQ.loc[:, 'roe_core_4Q'], x=statsQ.loc[:, 'dates'], name="roe_cốt lõi", yaxis='y2',
#                        line=dict(color='rgb(191, 214, 48)', width=3), mode='lines+markers')
#     test3 = go.Bar(y=statsQ.loc[:, 'op'], x=statsQ.loc[:, 'dates'], name='LNTT cốt lõi',
#                    marker=dict(color=('teal')))
#     test4 = go.Bar(y=-np.abs(statsQ.loc[:, 'int_exp']), x=statsQ.loc[:, 'dates'], name='Chi phí lãi vay',
#                    marker=dict(color=('goldenrod')))
#     test5 = go.Bar(y=statsQ.loc[:, 'fin_income'], x=statsQ.loc[:, 'dates'], name='LN tài chính',
#                    marker=dict(color=('#A4DE02')))
#     test6 = go.Bar(y=statsQ.loc[:, 'jv_income'], x=statsQ.loc[:, 'dates'], name='LN LDLK',
#                    marker=dict(color=('deeppink')))
#     test7 = go.Bar(y=statsQ.loc[:, 'other_income'], x=statsQ.loc[:, 'dates'], name='LN khác',
#                    marker=dict(color=('darkgray')))
#     test8 = go.Scatter(y=statsQ.loc[:, 'net_income'], x=statsQ.loc[:, 'dates'], name="LNST",
#                        line=dict(color='darkturquoise', width=3,dash='dot'), mode='lines')
#
#     roae = [test1, test2, test3, test4, test5, test6,test7,test8]
#     fig = go.Figure(data=roae,layout=go.Layout(barmode='relative',
#                                 title='Lợi nhuận trước thuế (Quý)',
#                                 xaxis=dict(tickformat='%Y-%b', showgrid=False),
#                                 yaxis2=go.layout.YAxis(tickformat='.1%', gridwidth=3, overlaying='y', side='right',
#                                                        showgrid=False)
#
#                                 , legend=dict(x=1.1, y=1)
#
#                                 # yaxis2=dict(title='Price',overlaying='y', side='right')
#                                 ))
#     return fig.update_layout(template='plotly_dark',title_x=0.5,
#                              plot_bgcolor='rgba(0, 0, 0, 0)',
#                              paper_bgcolor='rgba(0, 0, 0, 0)')
#
#
#
# @app.callback(
#     Output(component_id='output-graph3SQLQ', component_property='figure'),
#     [Input(component_id='intermediate-valueSQLQ', component_property='children')]
# )
# def asset(dat):
#     statsQ = pd.read_json(dat, orient='split')
#     asset_bar1 = go.Bar(y=statsQ.loc[:, "bs_cash"], x=statsQ.loc[:, "dates"], name='Tiền+ĐTNH',
#                         marker=dict(color=('teal')))
#     asset_bar2 = go.Bar(y=statsQ.loc[:, "bs_ar"], x=statsQ.loc[:, "dates"], name="Phải thu ngắn hạn",
#                         marker=dict(color=('#A4DE02')))
#     asset_bar3 = go.Bar(y=statsQ.loc[:, "net_inven"], x=statsQ.loc[:, "dates"], name="Hàng tồn kho",
#                         marker=dict(color=('green')))
#     asset_bar4 = go.Bar(y=statsQ.loc[:, "bs_fa"], x=statsQ.loc[:, "dates"], name="TSCĐ",
#                         marker=dict(color=('rgb(200, 0, 0)')))
#     asset_bar5 = go.Bar(y=statsQ.loc[:, "cip"], x=statsQ.loc[:, "dates"], name="XDCB",
#                         marker=dict(color=('goldenrod')))
#     asset_bar6 = go.Bar(y=statsQ.loc[:, "other_asset"], x=statsQ.loc[:, "dates"], name="Khác",
#                         marker=dict(color=('darkgray')))
#     asset_bar7 = go.Scatter(y=statsQ.loc[:, "ca/ta"], x=statsQ.loc[:, "dates"], yaxis='y2',
#                             name="TS ngắn hạn/Tổng tài sản", line=dict(color='darkturquoise', width=3),
#                             mode='lines+markers')
#     # asset_bar8 = go.Scatter(y=statsQ.loc[ticker, "mc"], x=statsQ.loc[ticker, "mc"].index, yaxis='y', name="Vốn hóa",
#     #                         line=dict(color='black', width=3), mode='lines+markers')
#     asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4, asset_bar5, asset_bar6, asset_bar7]
#
#     fig = go.Figure(data=asset_data,layout=go.Layout(barmode='relative'
#                                 , xaxis=dict(tickformat='%Y-%b', showgrid=False)
#                                 , yaxis=go.layout.YAxis(gridwidth=3  # ,hoverformat = '.1f'
#                                                         )
#                                 , yaxis2=go.layout.YAxis(showgrid=False, tickformat='%',
#                                                          overlaying='y', side='right', range=[0, 1])
#                                 , title='Cơ cấu tài sản'
#                                 , legend=dict(x=1.1, y=1)
#                                 ))
#
#     return fig.update_layout(template='plotly_dark',title_x=0.5,
#                              plot_bgcolor='rgba(0, 0, 0, 0)',
#                              paper_bgcolor='rgba(0, 0, 0, 0)')
#
# @app.callback(
#     Output(component_id='output-graph4SQLQ', component_property='figure'),
#     [Input(component_id='intermediate-valueSQLQ', component_property='children')]
# )
# def equity(dat):
#     statsQ = pd.read_json(dat, orient='split')
#     asset_bar1 = go.Bar(y=statsQ.loc[:, "cap_e"], x=statsQ.loc[:, "dates"], name="Vốn điều lệ",
#                         marker=dict(color=('teal')))
#     asset_bar2 = go.Bar(y=statsQ.loc[:, "re"], x=statsQ.loc[:, "dates"], name="LN chưa phân phối",
#                         marker=dict(color=('#A4DE02')))
#     asset_bar3 = go.Bar(y=statsQ.loc[:, "bs_treasury"], x=statsQ.loc[:, "dates"],
#                         name="Cổ phiếu quỹ", marker=dict(color=('pink')))
#     asset_bar4 = go.Bar(y=statsQ.loc[:, "other_equity"], x=statsQ.loc[:, "dates"],
#                         name="Vốn khác", marker=dict(color=('green')))
#     asset_bar5 = go.Bar(y=statsQ.loc[:, "bs_ap"], x=statsQ.loc[:, "dates"], name="Phải trả ngắn hạn",
#                         marker=dict(color=('#FFFF99')))
#     asset_bar6 = go.Bar(y=statsQ.loc[:, "st_debt"], x=statsQ.loc[:, "dates"], name='Vay ngắn hạn',
#                         marker=dict(color=('goldenrod')))
#     asset_bar7 = go.Bar(y=statsQ.loc[:, "lt_debt"], x=statsQ.loc[:, "dates"], name="Vay dài hạn",
#                         marker=dict(color=('rgb(200, 0, 0)')))
#     asset_bar8 = go.Bar(y=statsQ.loc[:, "bs_cust_pre"], x=statsQ.loc[:, "dates"], name="KH trả tiền trước",
#                         marker=dict(color=('deeppink')))
#     asset_bar9 = go.Bar(y=statsQ.loc[:, "other_lia"], x=statsQ.loc[:, "dates"], name="Nợ khác",
#                         marker=dict(color=('darkgray')))
#
#     # asset_bar9 = go.Scatter(y=statsQ.loc[ticker, "mc"], x=statsQ.loc[ticker, "mc"].index, name="Vốn hóa",
#     #                         line=dict(color='black', width=3), mode='lines+markers')
#     asset_bar10 = go.Scatter(y=statsQ.loc[:, "DE"], x=statsQ.loc[:, "dates"], yaxis='y2', name="D/E",
#                              line=dict(color='darkturquoise', width=3), mode='lines+markers')
#     asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4, asset_bar5, asset_bar6, asset_bar7, asset_bar8,
#                   asset_bar9, asset_bar10]
#
#     fig = go.Figure(data=asset_data,layout=go.Layout(barmode='relative'
#                                 , xaxis=dict(tickformat='%Y-%b', showgrid=False)
#                                 , yaxis2=go.layout.YAxis(showgrid=False, tickformat='.1%', overlaying='y',
#                                                          side='right')
#                                 , yaxis=go.layout.YAxis(gridwidth=3  # ,hoverformat = '.1f'
#                                                         )
#                                 , title='Cơ cấu nguồn vốn'
#                                 , legend=dict(x=1.1, y=1)
#                                 ))
#
#     return fig.update_layout(template='plotly_dark',title_x=0.5,
#                              plot_bgcolor='rgba(0, 0, 0, 0)',
#                              paper_bgcolor='rgba(0, 0, 0, 0)')

# @app.callback(
#     Output(component_id='output-graph1SQLQ7', component_property='figure'),
#     [Input(component_id='intermediate-valueSQLQ', component_property='children')]
# )
# def growth(ticker):
#     ticker = ticker.upper()
#     g1 = go.Scatter(y=statsQ.loc[ticker, "g_rev"], x=statsQ.loc[ticker, "g_rev"].index, name="Sales Growth", yaxis="y2",
#                     line=dict(color='red', width=3), mode='lines+markers')
#     g2 = go.Scatter(y=statsQ.loc[ticker, "g_core_e"], x=statsQ.loc[ticker, "g_core_e"].index, name="Core E Growth",
#                     yaxis="y2", line=dict(color='green', width=3), mode='lines+markers')
#     g3 = go.Scatter(y=statsQ.loc[ticker, "g_net_income"], x=statsQ.loc[ticker, "g_net_income"].index, name="NI Growth",
#                     yaxis="y2", line=dict(color='yellow', width=3), mode='lines+markers')
#     g4 = go.Bar(y=statsQ.loc[ticker, "mc"], x=statsQ.loc[ticker, "mc"].index, name='Vốn hóa',
#                 marker=dict(color=('rgb(20, 50, 90)')))
#
#     return {'data': [g1, g2, g3, g4],
#             'layout': go.Layout(title='Tăng trưởng',
#                                 xaxis=dict(tickvals=statsQ.loc[ticker].index, showgrid=False),
#                                 yaxis2=go.layout.YAxis(tickformat='.1%', gridwidth=3, overlaying="y", side="right",
#                                                        showgrid=False, range=[-0.5, 1])
#                                 , legend=dict(x=1.1, y=1)
#                                 )
#
#             }


# @app.callback(
#     Output(component_id='output-graph1SQLQ8', component_property='figure'),
#     [Input(component_id='intermediate-valueSQLQ', component_property='children')]
# )
# def cf(ticker):
#     ticker = ticker.upper()
#     bar1 = go.Bar(y=statsQ.loc[ticker, "net_income"], x=statsQ.loc[ticker, "net_income"].index, name='Lãi/Lỗ',
#                   marker=dict(color='rgb(20, 50, 90)'))
#     bar2 = go.Bar(y=statsQ.loc[ticker, "graph_dep"], x=statsQ.loc[ticker, "graph_dep"].index, name="Khấu hao",
#                   marker=dict(color='#A4DE02'))
#     bar3 = go.Bar(y=statsQ.loc[ticker, "e_raise"], x=statsQ.loc[ticker, "e_raise"].index, name="Tăng vốn",
#                   marker=dict(color='purple'))
#     bar4 = go.Bar(y=statsQ.loc[ticker, "div"], x=statsQ.loc[ticker, "div"].index, name="Cổ tức tiền mặt và cp quỹ",
#                   marker=dict(color='red'))
#     bar5 = go.Bar(y=statsQ.loc[ticker, "cf_delta_debt"], x=statsQ.loc[ticker, "cf_delta_debt"].index,
#                   name="Vay thêm/trả", marker=dict(color='orange'))
#     bar6 = go.Bar(y=statsQ.loc[ticker, "cf_capex"], x=statsQ.loc[ticker, "cf_capex"].index, name="Capex",
#                   marker=dict(color='yellow'))
#     bar7 = go.Bar(y=statsQ.loc[ticker, "bs_delta_wc"], x=statsQ.loc[ticker, "bs_delta_wc"].index,
#                   name="Thay đổi vốn lưu động", marker=dict(color='pink'))
#     bar10 = go.Bar(y=statsQ.loc[ticker, "cf_khac"], x=statsQ.loc[ticker, "cf_khac"].index, name="CF khác",
#                    marker=dict(color='grey'))
#     tong = go.Scatter(y=statsQ.loc[ticker, "cf_tong"], x=statsQ.loc[ticker, "cf_tong"].index,
#                       name="Tổng dòng tiền (phải)", yaxis='y2', line=dict(color='black', width=3), mode='lines+markers')
#     data_CF = [bar1, bar2, bar3, bar4, bar5, bar6, bar7, bar10, tong]
#
#     return {'data': data_CF,
#             'layout': go.Layout(barmode='relative',
#                                 xaxis=dict(tickvals=statsQ.loc[ticker].index)
#                                 , yaxis=go.layout.YAxis(gridwidth=3, rangemode='tozero'  # hoverformat = '.1f'
#                                                         )
#                                 ,
#                                 yaxis2=go.layout.YAxis(overlaying='y', side='right', showgrid=False, rangemode='tozero')
#                                 , title='Cơ cấu dòng tiền'
#                                 , legend=dict(x=1.1, y=1)
#                                 )
#
#             }
#
#
# @app.callback(
#     Output(component_id='output-graph1SQLQ5', component_property='figure'),
#     [Input(component_id='intermediate-valueSQLQ', component_property='children')]
# )
# def pe(ticker):
#     ticker = ticker.upper()
#     bar1 = go.Scatter(y=statsQ.loc[ticker, "net_income"], x=statsQ.loc[ticker, "net_income"].index, name='Lãi/Lỗ 4Q',
#                       line=dict(color='rgb(20, 50, 90)', width=3), mode='lines+markers')
#     bar2 = go.Scatter(y=statsQ.loc[ticker, "core_e"], x=statsQ.loc[ticker, "core_e"].index, name='Lãi/Lỗ core 4Q',
#                       line=dict(color='#A4DE02', width=3), mode='lines+markers')
#     bar3 = go.Scatter(y=statsQ.loc[ticker, "mc"], x=statsQ.loc[ticker, "mc"].index, name="Vốn hóa (phải)",
#                       line=dict(color='red', width=3), mode='lines+markers', yaxis='y2')
#
#     data_PE = [bar1, bar2, bar3]
#
#     return {'data': data_PE,
#             'layout': go.Layout(xaxis=dict(showgrid=False)
#                                 , yaxis=go.layout.YAxis(gridwidth=3)
#                                 , yaxis_type='log'
#                                 , yaxis2=go.layout.YAxis(overlaying='y', side='right', showgrid=False)
#                                 , title='P/E'
#                                 , legend=dict(x=1.1, y=1)
#                                 )
#
#             }


# @app.callback(
#     Output(component_id='output-graph1SQLQ6', component_property='figure'),
#     [Input(component_id='intermediate-valueSQLQ', component_property='children')]
# )
# def pb(ticker):
#     ticker = ticker.upper()
#     bar1 = go.Scatter(y=statsQ.loc[ticker, "te"], x=statsQ.loc[ticker, "te"].index, name='Book value',
#                       line=dict(color='rgb(20, 50, 90)', width=3), mode='lines+markers')
#     bar2 = go.Scatter(y=statsQ.loc[ticker, "mc"], x=statsQ.loc[ticker, "mc"].index, name='Vốn hóa',
#                       line=dict(color='red', width=3), mode='lines+markers')
#     bar3 = go.Scatter(y=statsQ.loc[ticker, "roe"], x=statsQ.loc[ticker, "roe"].index, name="ROE (phải)",
#                       line=dict(color='#A4DE02', width=3), mode='lines+markers', yaxis='y2')
#     bar4 = go.Scatter(y=statsQ.loc[ticker, "roe_core"], x=statsQ.loc[ticker, "roe_core"].index, name="ROE_core (phải)",
#                       line=dict(color='orange', width=3), mode='lines+markers', yaxis='y2')
#
#     data_PB = [bar1, bar2, bar3, bar4]
#
#     return {'data': data_PB,
#             'layout': go.Layout(barmode='relative',
#                                 xaxis=dict(
#                                     showgrid=False)
#                                 , yaxis=go.layout.YAxis(gridwidth=3)
#                                 , yaxis_type="log"
#                                 , yaxis2=go.layout.YAxis(tickformat='.1%', overlaying='y', side='right', showgrid=False,
#                                                          rangemode='tozero')
#                                 , title='P/B'
#                                 , legend=dict(x=1.1, y=1)
#                                 )
#
#             }

# app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

# if __name__ == '__main__':
#    app.run_server(debug=True)
#
