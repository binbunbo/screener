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
import dash_bootstrap_components as dbc
idx = pd.IndexSlice
from app import server

df = pd.read_pickle('D:/Data/df_listed_full')
col1 = ['gp', 'op', 'op1', 'EBT', 'pretax_inc', 'net_income', 'ni_parent', 'core_e']
col2 = ['rev', 'gp', 'op', 'EBT', 'pretax_inc', 'net_income', 'ni_parent', 'core_e', 'rev_4Q', 'gp_4Q', 'op_4Q',
        'pretax_inc_4Q', 'net_income_4Q', 'ni_parent_4Q', 'core_e_4Q']
col3 = ['rev', 'gp', 'op', 'EBT', 'pretax_inc', 'net_income', 'ni_parent', 'core_e']
def get_price(ticker):
    url = 'https://finfo-api.vndirect.com.vn/v4/ratios?q=code:'+ticker+'~itemCode:51003'
    try:
        r = requests.get(url)
        raw = pd.json_normalize(json.loads(r.content)['data'])
        fs = raw[['code','value','reportDate']]
        return fs
    except:
        print('Có lỗi, xin nhập mã khác')
def get_mc(ticker):
    url = 'https://finance.vietstock.vn/Account/Login'
    payload = {'Email': 'nhathoang.nguyen.20@gmail.com','Password': 'Rm!t20071993'}
    with requests.Session() as s:
        p = s.post(url, data=payload)
        url2 = 'https://finance.vietstock.vn/data/ExportTradingResult?Code='+ticker+'&OrderBy=&OrderDirection=desc&PageIndex=1&PageSize=10&FromDate=2004-01-01&ToDate=2021-05-11&ExportType=excel&Cols=TKLGD%2CTGTGD%2CVHTT%2CTGG%2CDC%2CTGPTG%2CKLGDKL%2CGTGDKL&ExchangeID=1'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}
        r = requests.get(url2,headers=headers)
        df = pd.read_html(r.content,encoding='utf-8')[1].iloc[:,[0,3]]
        df.columns = ['dates','mc']
        df['dates'] = pd.to_datetime(df['dates'], format='%d/%m/%Y')
        df['mc'] = df['mc'].astype(float)*(10**9)
        df['year'] = df['dates'].dt.year
        df['quarter'] = df['dates'].dt.quarter
        df['Ticker']=ticker
        df = df.sort_values('dates',ascending=True).groupby(['Ticker','year','quarter'])[['mc']].apply(lambda x: x.iloc[-1])
        return df
def get_df(ticker):
    try:
        return df.loc[idx[:,ticker,:,[1,2,3,4]],:]
    except:
        print('Có lỗi, xin nhập mã khác')

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

def g_func(x, i):
    x["g_" + i] = x.sort_index(level=[0,1,2]).groupby(level=[0])[i].diff(periods=3) / np.abs(x[i].sort_index(level=[0,1,2]).shift(3))

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
    x['cf_tong'] = x['cfo'] + x['cfi'] + x['cff']
    x['cf_khac'] = x['cf_tong'] - x['net_income'] - x['cf_dep'] - x['cf_e_raise'] - x['cf_div'] - x['cf_treasury'] - x[
        'cf_capex']
    x['P/E'] = x['mc'] / x['net_income_4Q']
    x['P/B'] = x['mc'] / x['te']

def add_df(ticker):
    ticker = ticker.upper()
    x = get_df(ticker)
    y = get_mc(ticker)
    x = x.reset_index()
    x = x.set_index(['Ticker','year','quarter'])
    x = pd.merge(y, x, on=['Ticker','year', 'quarter'],how='left')
    add_ratios(x)
    for i in col3:
        ttm(x, i)
    for i in col1:
        margin_func(x, i)
    for i in col2:
        g_func(x, i)
    add_stats(x)
    return x


layout = html.Div(children=[
    html.Header(children='Graph công ty thường Quý', className='ml-4',
                style={'font-size': '30px', 'font-weight': 'bold', 'font-family': 'Arial', 'text-align': 'center'}),
    html.Div(children='''Chọn mã CK và nhấn Enter:''', className='ml-4', style={'font-size': '20px'}),
    dcc.Input(id='input', value='VNM', type='text', debounce=True, className='ml-4'),
    html.Br(),
    html.Br(),
    dbc.Container(id='price-SQLQ',className='six columns',
                 style={'width': '30%', 'display': 'inline-block','margin-left':'5px'}),
    html.Div(id='intermediate-valueSQLQ', style={'display': 'none'}),
    html.Div([
        html.Div([dcc.Graph(id='output-graph1SQLQ')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph2SQLQ')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph3SQLQ')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph4SQLQ')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph5SQLQ')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph6SQLQ')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph7SQLQ')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph8SQLQ')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row')
])
@app.callback(Output('price-SQLQ', 'children'),
              [Input(component_id='input', component_property='value')])
def display_price(ticker):
    price = get_price(ticker)
    mc = price['value']/1000000000
    text = 'Vốn hóa của ' + price['code'].values[0] + ' tại ' + price['reportDate'].values[0] + ' là: ' + mc.map('{:,.0f}'.format).values[0] + ' tỷ VND'
    alert = dbc.Alert(text,dismissable=False,is_open=True,color="success")
    return alert
@app.callback(Output('intermediate-valueSQLQ', 'children'), [Input(component_id='input', component_property='value')])
def clean_data(ticker):
    statsQ = add_df(ticker)
    statsQ = statsQ.reset_index()
    statsQ = statsQ.set_index('Ticker')
    # statsQ = statsQ.replace(np.nan,0)
    statsQ['dates'] = pd.PeriodIndex(year=statsQ.reset_index()["year"], quarter=statsQ.reset_index()["quarter"])
    statsQ['dates'] = statsQ['dates'].dt.to_timestamp(freq='Q')
    return statsQ.to_json(date_format='iso', orient='split')


@app.callback(
    Output(component_id='output-graph1SQLQ', component_property='figure'),
    [Input(component_id='intermediate-valueSQLQ', component_property='children')]
)
def profit(dat):
    statsQ = pd.read_json(dat, orient='split')
    test = go.Scatter(y=statsQ.loc[:, "gpm"], x=statsQ.loc[:, "dates"], name="Gross Margin", yaxis='y2',
                      line=dict(color='red', width=3), mode='lines')
    test2 = go.Scatter(y=statsQ.loc[:, "EBTm"], x=statsQ.loc[:, "dates"], name="OP Margin (inc. ir)",
                       yaxis='y2', line=dict(color='rgb(191, 214, 48)', width=3), mode='lines')
    test3 = go.Scatter(y=statsQ.loc[:, "net_incomem"], x=statsQ.loc[:, "dates"],
                       name="Net Margin", yaxis='y2', line=dict(color='darkturquoise', width=3), mode='lines')
    test4 = go.Bar(y=statsQ.loc[:, "rev"], x=statsQ.loc[:, "dates"], name='Doanh thu thuần',
                   marker=dict(color=('teal')))
    data_set = [test, test2, test3, test4]
    fig = go.Figure(data=data_set,layout=dict(title='Doanh thu và tỷ suất LN',
                           xaxis=dict(tickformat='%Y-%b', showgrid=False),
                           yaxis=go.layout.YAxis(  # hoverformat = '.1f'
                           )
                           , yaxis2=go.layout.YAxis(tickformat='.1%', gridwidth=3, showgrid=False,
                                                    overlaying='y', side='right')
                           , legend=dict(x=1.1, y=1)
                           ))
    return fig.update_layout( template='plotly_dark',title_x=0.5,
                        plot_bgcolor= 'rgba(0, 0, 0, 0)',
                        paper_bgcolor= 'rgba(0, 0, 0, 0)')

@app.callback(
    Output(component_id='output-graph2SQLQ', component_property='figure'),
    [Input(component_id='intermediate-valueSQLQ', component_property='children')]
)
def roae(dat):
    statsQ = pd.read_json(dat, orient='split')

    test1 = go.Scatter(y=statsQ.loc[:, 'roe_4Q'], x=statsQ.loc[:, 'dates'], name="roe", yaxis='y2',
                       line=dict(color='red', width=3), mode='lines')
    test2 = go.Scatter(y=statsQ.loc[:, 'roe_core_4Q'], x=statsQ.loc[:, 'dates'], name="roe_cốt lõi", yaxis='y2',
                       line=dict(color='rgb(191, 214, 48)', width=3), mode='lines')
    test3 = go.Bar(y=statsQ.loc[:, 'op'], x=statsQ.loc[:, 'dates'], name='LNTT cốt lõi',
                   marker=dict(color=('teal')))
    test4 = go.Bar(y=-np.abs(statsQ.loc[:, 'int_exp']), x=statsQ.loc[:, 'dates'], name='Chi phí lãi vay',
                   marker=dict(color=('goldenrod')))
    test5 = go.Bar(y=statsQ.loc[:, 'fin_income'], x=statsQ.loc[:, 'dates'], name='LN tài chính',
                   marker=dict(color=('#A4DE02')))
    test6 = go.Bar(y=statsQ.loc[:, 'jv_income'], x=statsQ.loc[:, 'dates'], name='LN LDLK',
                   marker=dict(color=('deeppink')))
    test7 = go.Bar(y=statsQ.loc[:, 'other_income'], x=statsQ.loc[:, 'dates'], name='LN khác',
                   marker=dict(color=('darkgray')))
    test8 = go.Scatter(y=statsQ.loc[:, 'net_income'], x=statsQ.loc[:, 'dates'], name="LNST",
                       line=dict(color='darkturquoise', width=3,dash='dot'), mode='lines')

    roae = [test1, test2, test3, test4, test5, test6,test7,test8]
    fig = go.Figure(data=roae,layout=go.Layout(barmode='relative',
                                title='Lợi nhuận trước thuế (Quý)',
                                xaxis=dict(tickformat='%Y-%b', showgrid=False),
                                yaxis2=go.layout.YAxis(tickformat='.1%', gridwidth=3, overlaying='y', side='right',
                                                       showgrid=False)

                                , legend=dict(x=1.1, y=1)

                                # yaxis2=dict(title='Price',overlaying='y', side='right')
                                ))
    return fig.update_layout(template='plotly_dark',title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')

@app.callback(
    Output(component_id='output-graph3SQLQ', component_property='figure'),
    [Input(component_id='intermediate-valueSQLQ', component_property='children')]
)
def asset(dat):
    statsQ = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsQ.loc[:, "bs_cash"], x=statsQ.loc[:, "dates"], name='Tiền+ĐTNH',
                        marker=dict(color=('teal')))
    asset_bar2 = go.Bar(y=statsQ.loc[:, "bs_ar"], x=statsQ.loc[:, "dates"], name="Phải thu ngắn hạn",
                        marker=dict(color=('#A4DE02')))
    asset_bar3 = go.Bar(y=statsQ.loc[:, "net_inven"], x=statsQ.loc[:, "dates"], name="Hàng tồn kho",
                        marker=dict(color=('green')))
    asset_bar4 = go.Bar(y=statsQ.loc[:, "bs_fa"], x=statsQ.loc[:, "dates"], name="TSCĐ",
                        marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar5 = go.Bar(y=statsQ.loc[:, "cip"], x=statsQ.loc[:, "dates"], name="XDCB",
                        marker=dict(color=('goldenrod')))

    asset_bar6 = go.Bar(y=statsQ.loc[:, "other_asset"], x=statsQ.loc[:, "dates"], name="Khác",
                        marker=dict(color=('darkgray')))
    asset_bar7 = go.Scatter(y=statsQ.loc[:, "ca/ta"], x=statsQ.loc[:, "dates"], yaxis='y2',
                            name="TS ngắn hạn/Tổng tài sản", line=dict(color='deeppink', width=3, dash='dot'),
                            mode='lines')
    asset_bar8 = go.Scatter(y=statsQ.loc[:, "mc"], x=statsQ.loc[:, "dates"], yaxis='y', name="Vốn hóa",
                            line=dict(color='darkturquoise', width=3), mode='lines+markers')
    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4, asset_bar5, asset_bar6, asset_bar7,asset_bar8]

    fig = go.Figure(data=asset_data,layout=go.Layout(barmode='relative'
                                , xaxis=dict(tickformat='%Y-%b', showgrid=False)
                                , yaxis=go.layout.YAxis(gridwidth=3  # ,hoverformat = '.1f'
                                                        )
                                , yaxis2=go.layout.YAxis(showgrid=False, tickformat='%',
                                                         overlaying='y', side='right', range=[0, 1])
                                , title='Cơ cấu tài sản'
                                , legend=dict(x=1.1, y=1)
                                ))

    return fig.update_layout(template='plotly_dark',title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')

@app.callback(
    Output(component_id='output-graph4SQLQ', component_property='figure'),
    [Input(component_id='intermediate-valueSQLQ', component_property='children')]
)
def equity(dat):
    statsQ = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsQ.loc[:, "cap_e"], x=statsQ.loc[:, "dates"], name="Vốn điều lệ",
                        marker=dict(color=('teal')))
    asset_bar2 = go.Bar(y=statsQ.loc[:, "re"], x=statsQ.loc[:, "dates"], name="LN chưa phân phối",
                        marker=dict(color=('#A4DE02')))
    asset_bar3 = go.Bar(y=statsQ.loc[:, "bs_treasury"], x=statsQ.loc[:, "dates"],
                        name="Cổ phiếu quỹ", marker=dict(color=('pink')))
    asset_bar4 = go.Bar(y=statsQ.loc[:, "other_equity"], x=statsQ.loc[:, "dates"],
                        name="Vốn khác", marker=dict(color=('green')))
    asset_bar5 = go.Bar(y=statsQ.loc[:, "bs_ap"], x=statsQ.loc[:, "dates"], name="Phải trả ngắn hạn",
                        marker=dict(color=('#FFFF99')))
    asset_bar6 = go.Bar(y=statsQ.loc[:, "st_debt"], x=statsQ.loc[:, "dates"], name='Vay ngắn hạn',
                        marker=dict(color=('goldenrod')))
    asset_bar7 = go.Bar(y=statsQ.loc[:, "lt_debt"], x=statsQ.loc[:, "dates"], name="Vay dài hạn",
                        marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar8 = go.Bar(y=statsQ.loc[:, "bs_cust_pre"], x=statsQ.loc[:, "dates"], name="KH trả tiền trước",
                        marker=dict(color=('deeppink')))
    asset_bar9 = go.Bar(y=statsQ.loc[:, "other_lia"], x=statsQ.loc[:, "dates"], name="Nợ khác",
                        marker=dict(color=('darkgray')))

    asset_bar10 = go.Scatter(y=statsQ.loc[:, "mc"], x=statsQ.loc[:, "dates"], name="Vốn hóa",
                             line=dict(color='darkturquoise', width=3), mode='lines+markers')
    asset_bar11 = go.Scatter(y=statsQ.loc[:, "DE"], x=statsQ.loc[:, "dates"], yaxis='y2', name="D/E",
                             line=dict(color='deeppink', width=3, dash='dot'), mode='lines')
    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4, asset_bar5, asset_bar6, asset_bar7, asset_bar8,
                  asset_bar9, asset_bar10, asset_bar11]

    fig = go.Figure(data=asset_data,layout=go.Layout(barmode='relative'
                                , xaxis=dict(tickformat='%Y-%b', showgrid=False)
                                , yaxis2=go.layout.YAxis(showgrid=False, tickformat='.1%', overlaying='y',
                                                         side='right')
                                , yaxis=go.layout.YAxis(gridwidth=3  # ,hoverformat = '.1f'
                                                        )
                                , title='Cơ cấu nguồn vốn'
                                , legend=dict(x=1.1, y=1)
                                ))

    return fig.update_layout(template='plotly_dark',title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')

@app.callback(
    Output(component_id='output-graph5SQLQ', component_property='figure'),
    [Input(component_id='intermediate-valueSQLQ', component_property='children')]
)
def growth(dat):
    statsQ = pd.read_json(dat, orient='split')
    g1 = go.Scatter(y=statsQ.loc[:, "g_rev"], x=statsQ.loc[:, "dates"], name="Tăng trưởng doanh thu",
                    line=dict(color='teal', width=3), mode='lines+markers')
    g2 = go.Scatter(y=statsQ.loc[:, "g_op"], x=statsQ.loc[:, "dates"], name="Tăng trưởng LN cốt lõi",
                    line=dict(color='rgb(191, 214, 48)', width=3), mode='lines+markers')
    g3 = go.Scatter(y=statsQ.loc[:, "g_net_income"], x=statsQ.loc[:, "dates"], name="Tăng trưởng LNST",
                    line=dict(color='red', width=3), mode='lines+markers')
    g = [g1, g2, g3]
    fig = go.Figure(data=g, layout=go.Layout(barmode='relative'
                                                      , xaxis=dict(tickformat='%Y-%b', showgrid=False)
                                                      , yaxis=go.layout.YAxis(showgrid=False, tickformat='.1%',
                                                                               overlaying='y'
                                                                               )

                                                      , title='Tăng trưởng quý (YoY)'
                                                      , legend=dict(x=1.1, y=1)
                                                      ))

    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')

@app.callback(
    Output(component_id='output-graph6SQLQ', component_property='figure'),
    [Input(component_id='intermediate-valueSQLQ', component_property='children')]
)
def cf(dat):
    statsQ = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsQ.loc[:, "net_income"], x=statsQ.loc[:, "dates"], name="LNST",
                        marker=dict(color=('teal')))
    asset_bar2 = go.Bar(y=statsQ.loc[:, "cf_dep"], x=statsQ.loc[:, "dates"], name="Khấu hao",
                        marker=dict(color=('#A4DE02')))
    asset_bar3 = go.Bar(y=statsQ.loc[:, "cf_e_raise"], x=statsQ.loc[:, "dates"], name="Tăng vốn",
                        marker=dict(color='deeppink'))
    asset_bar4 = go.Bar(y=statsQ.loc[:, "cf_div"], x=statsQ.loc[:, "dates"],
                        name="Cổ tức tiền mặt", marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar5 = go.Bar(y=statsQ.loc[:, "cf_treasury"], x=statsQ.loc[:, "dates"], name="CP quỹ",
                        marker=dict(color=('goldenrod')))
    asset_bar6 = go.Bar(y=statsQ.loc[:, "cf_capex"], x=statsQ.loc[:, "dates"], name="Đầu tư TSCĐ",
                        marker=dict(color=('#FFFF99')))
    asset_bar7 = go.Bar(y=statsQ.loc[:, "cf_khac"], x=statsQ.loc[:, "dates"], name='CF khác',
                        marker=dict(color=('darkgray')))
    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4, asset_bar5, asset_bar6,asset_bar7]

    fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'
                                , xaxis=dict(tickformat='%Y-%b')
                                # , yaxis2=go.layout.YAxis(showgrid=False, tickformat='.1%', title='D/A', overlaying='y',
                                #                          side='right')
                                , yaxis=go.layout.YAxis(gridwidth=3  # ,hoverformat = '.1f'
                                                        )
                                , title='Dòng tiền'
                                , legend=dict(x=1.1, y=1)
                                ))

    return fig.update_layout(template='plotly_dark',title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')
@app.callback(
    Output(component_id='output-graph7SQLQ', component_property='figure'),
    [Input(component_id='intermediate-valueSQLQ', component_property='children')]
)
def pe(dat):
    statsQ = pd.read_json(dat, orient='split')
    bar1 = go.Scatter(y=statsQ.loc[:, "net_income_4Q"], x=statsQ.loc[:, "dates"], name='LNST 4Q',
                      line=dict(color='red', width=3,dash='dot'), mode='lines')
    bar2 = go.Scatter(y=statsQ.loc[:, "core_e_4Q"], x=statsQ.loc[:, "dates"], name='LNST cốt lõi 4Q',
                      line=dict(color='rgb(191, 214, 48)', width=3,dash='dot'), mode='lines')
    bar3 = go.Scatter(y=statsQ.loc[:, "mc"], x=statsQ.loc[:, "dates"], name="Vốn hóa (phải)",
                      line=dict(color='darkturquoise', width=3), mode='lines+markers', yaxis='y')
    bar4 = go.Scatter(y=statsQ.loc[:, "P/E"], x=statsQ.loc[:, "dates"], name="P/E (phải)",
                      line=dict(color='lavender', width=3),
                      mode='lines', yaxis='y2')

    data_PE = [bar1, bar2, bar3,bar4]
    fig = go.Figure(data=data_PE, layout=go.Layout(xaxis=dict(showgrid=False,tickformat='%Y-%b')
                                , yaxis=go.layout.YAxis(gridwidth=3)
                                , yaxis_type='log'
                                , yaxis2=go.layout.YAxis(overlaying='y', side='right', showgrid=False
                                                         ,range=[0,30],)
                                , title='P/E'
                                , legend=dict(x=1.1, y=1)
                                ))

    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')

@app.callback(
    Output(component_id='output-graph8SQLQ', component_property='figure'),
    [Input(component_id='intermediate-valueSQLQ', component_property='children')]
)
def pb(dat):
    statsQ = pd.read_json(dat, orient='split')
    bar1 = go.Scatter(y=statsQ.loc[:, "te"], x=statsQ.loc[:, "dates"], name='Giá trị số sách',
                      line=dict(color='lavender', width=3), mode='lines+markers')
    bar2 = go.Scatter(y=statsQ.loc[:, "mc"], x=statsQ.loc[:, "dates"], name='Vốn hóa',
                      line=dict(color='darkturquoise', width=3), mode='lines+markers')
    bar3 = go.Scatter(y=statsQ.loc[:, "roe_4Q"], x=statsQ.loc[:, "dates"], name="ROE (phải)",
                      line=dict(color='red', width=3,dash='dot'), mode='lines', yaxis='y2')
    bar4 = go.Scatter(y=statsQ.loc[:, "roe_core_4Q"], x=statsQ.loc[:, "dates"], name="ROE_core (phải)",
                      line=dict(color='rgb(191, 214, 48)', width=3,dash='dot'), mode='lines', yaxis='y2')

    data_PB = [bar1, bar2, bar3, bar4]

    fig = go.Figure(data=data_PB, layout=go.Layout(xaxis=dict(showgrid=False,tickformat='%Y-%b')
                                                   , yaxis=go.layout.YAxis(gridwidth=3)
                                                   , yaxis_type='log'
                                                   , yaxis2=go.layout.YAxis(overlaying='y', side='right',rangemode='tozero',
                                                                            showgrid=False,tickformat=".1%")
                                                   , title='P/B'
                                                   , legend=dict(x=1.1, y=1)
                                                   ))

    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')

# app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

# if __name__ == '__main__':
#    app.run_server(debug=True)
#
