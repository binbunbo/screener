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
from app import server

col = pd.read_excel('D:/Data/6.Python/project2/VND-col.xlsx')
col1 = ['gp', 'op', 'op1', 'EBT', 'pretax_inc', 'net_income', 'ni_parent', 'core_e']
col3 = ['rev', 'gp', 'op', 'EBT', 'pretax_inc', 'net_income', 'ni_parent', 'core_e']
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
        df['ticker']=ticker
        df = df.sort_values('dates',ascending=True).groupby(['ticker','year'])[['mc']].apply(lambda x: x.iloc[-1])
        return df
def get_price(ticker):
    url = 'https://finfo-api.vndirect.com.vn/v4/ratios?q=code:'+ticker+'~itemCode:51003'
    try:
        r = requests.get(url)
        raw = pd.json_normalize(json.loads(r.content)['data'])
        fs = raw[['code','value','reportDate']]
        return fs
    except:
        print('Có lỗi, xin nhập mã khác')
def get_dfY(ticker):
    url = 'https://finfo-api.vndirect.com.vn/v3/stocks/financialStatement?secCodes=' + ticker + '&reportTypes=ANNUAL&modelTypes=1,2,3,89,90,91,101,102,103,411,412,413&fromDate=2000-12-31&toDate=2021-12-31'
    try:
        r = requests.get(url)
        raw = pd.json_normalize(json.loads(r.content)['data']['hits'])
        fs = raw[['_source.secCode', '_source.fiscalDate', '_source.itemName', '_source.numericValue',
                  '_source.modelType']]
        fs.columns = ['ticker', 'dates', 'item', 'value', 'type']
        fs.loc[:, 'dates'] = pd.to_datetime(fs['dates'])
        fs.loc[:, 'year'] = fs['dates'].dt.year
        fs.loc[:, 'value'] = fs['value'].astype(float)
        fs = fs.drop(fs[(fs['item'].str.contains('kế toán trước thuế')) & (fs['type'] == 3)].index)
        fs = fs.pivot_table(values='value', index=['ticker', 'year'], columns='item')
        fs = fs.rename(columns=dict(zip(col['item'], col['col'])))
        del fs['drop']
        return fs
    except:
        print('Có lỗi, xin nhập mã khác')

def margin_func(x, i):
    x[i + "m"] = x[i] / x['rev']

def add_ratios(x):
    x['jv_income'] = x['jv_inc1'] + x['jv_inc2']
    x['cip'] = x['cip1']
    x['tax_rate'] = 1 - (x['net_income']/x['pretax_inc'])
    x['op'] = x['gp'] - (x['admin_exp']) - (x['sel_exp'])
    x['op1'] = x['op'] + x['jv_income']
    x['EBT'] = x['op'] - (x['int_exp'])
    x['fin_income'] = x['fin_rev'] - (x['fin_exp'] - x['int_exp'])
    x['other_income'] = x['other_rev'] - x['other_exp']
    x['bs_gross_fa'] = x['gross_tfa'] + x['gross_ifa'] + x['gross_lease'] + x['gross_ip']
    x['bs_fa'] = x['net_tfa'] + x['net_ifa'] + x['net_ip'] + x['net_lease']
    x['bs_cash'] = (x['cce'] + x['net_st_inv'])
    x['bs_capex'] = -(x.sort_index(level=[0, 1]).groupby(level=0)["bs_fa"].diff(periods=1) +
                      x.sort_index(level=[0, 1]).groupby(level=0)["cip"].diff(periods=1))
    x['bs_ar'] = x['st_ar']
    x['bs_ap'] = x['st_trade_ap']
    x['bs_cust_pre'] = x['st_prepaid_cust'] +x['lt_prepaid_cust'] +x['st_unrev'] + x['lt_unrev']
    x['debt'] = x['st_debt'] + x['lt_debt']
    x['core_e'] = x['op'] * (1 - x['tax_rate'])
    x['op2'] = x['core_e'] + x['jv_income']
    x['netcash'] = (x['bs_cash'] - x['cl'])
    x['ic'] = x['te'] + x['debt']
    x['other_asset'] = x['ta'] - x['bs_cash'] - x['bs_ar'] - x['net_inven'] - x['bs_fa'] - x['cip'] - x['bs_jv']
    x['other_lia'] = x['tl'] - x['debt'] - x['bs_ap'] - x['bs_cust_pre']
    x['other_equity'] = x['te'] - x['re'] - x['cap_e'] - x['bs_treasury']
    x['div'] = x['cf_div']+x['cf_treasury']
    x['cf_delta_debt'] = x['cf_divay'] + x['cf_debt_paid'] + x['cf_lease_paid']
    x['cf_khac'] = (x['cfo']+x['cfi']+x['cff'])-(x['cf_capex']+x['net_income']+x['cf_dep']
                                                 +x['cf_e_raise']+x['cf_delta_debt']+x['div'])


def g_func(x, i):
    x["g_" + i] = x.sort_index(level=[0, 1]).groupby(level=[0])[i].diff(periods=1) / np.abs(
        x[i].sort_index(level=[0, 1]).shift(1))

def add_stats(x):
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
    x['P/E'] = x['mc'] / x['net_income']
    x['P/B'] = x['mc'] / x['te']
def add_dfY(ticker):
    ticker = ticker.upper()
    x = get_dfY(ticker)
    y = get_mc(ticker)
    x = x.reset_index()
    x = x.set_index(['ticker', 'year'])
    x = pd.merge(y, x, on=['ticker', 'year'], how='left')
    add_ratios(x)
    for i in col1:
        margin_func(x,i)
    for i in col3:
        g_func(x, i)
    add_stats(x)
    return x

layout = html.Div(children=[
    html.Header(children='Graph Năm công ty thường ', className='ml-4',
                style={'font-size': '30px', 'font-weight': 'bold', 'font-family': 'Arial', 'text-align': 'center'}),
    html.Div(children='''Chọn mã CK và nhấn Enter:''', className='ml-4', style={'font-size': '20px'}),
    dcc.Input(id='input-Y', value='VNM', type='text', debounce=True, className='ml-4'),
    html.Div(id='intermediate-value-thuongY', style={'display': 'none'}),
    html.Br(),
    html.Br(),
    dbc.Container(id='price-thuongY',className='six columns',
                 style={'width': '30%', 'display': 'inline-block','margin-left':'5px'}),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-thuongY-1')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-thuongY-2')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-thuongY-3')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-thuongY-4')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-thuongY-5')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-thuongY-6')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
html.Div([
        html.Div([dcc.Graph(id='output-graph-thuongY-7')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-thuongY-8')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row')

])
@app.callback(Output('price-thuongY', 'children'),
              [Input(component_id='input-Y', component_property='value')])

def display_price(ticker):
    price = get_price(ticker)
    mc = price['value']/1000000000
    text = 'Vốn hóa của ' + price['code'].values[0] + ' tại ' + price['reportDate'].values[0] + ' là: ' + mc.map('{:,.0f}'.format).values[0] + ' tỷ VND'
    alert = dbc.Alert(text,dismissable=False,is_open=True,color="success")
    return alert

@app.callback(Output('intermediate-value-thuongY', 'children'), [Input(component_id='input-Y', component_property='value')])
def clean_data(ticker):
    statsY = add_dfY(ticker)
    statsY = statsY.reset_index()
    statsY = statsY.set_index('ticker')
    return statsY.to_json(date_format='iso', orient='split')

@app.callback(
    Output(component_id='output-graph-thuongY-1', component_property='figure'),
    [Input(component_id='intermediate-value-thuongY', component_property='children')]
)
def profit(dat):
    statsY = pd.read_json(dat, orient='split')
    test = go.Scatter(y=statsY.loc[:, "gpm"], x=statsY.loc[:, "year"], name="Gross Margin", yaxis='y2',
                      line=dict(color='red', width=3), mode='lines+markers')
    test2 = go.Scatter(y=statsY.loc[:, "EBTm"], x=statsY.loc[:, "year"], name="OP Margin (inc. ir)",
                       yaxis='y2', line=dict(color='rgb(191, 214, 48)', width=3), mode='lines+markers')
    test3 = go.Scatter(y=statsY.loc[:, "net_incomem"], x=statsY.loc[:, "year"],
                       name="Net Margin", yaxis='y2', line=dict(color='darkturquoise', width=3), mode='lines+markers')
    test4 = go.Bar(y=statsY.loc[:, "rev"], x=statsY.loc[:, "year"], name='Doanh thu thuần',
                   marker=dict(color=('teal')))
    data_set = [test, test2, test3, test4]

    fig = go.Figure(data=data_set, layout=dict(title='Doanh thu và tỷ suất LN',
                                               xaxis=dict(tickvals=statsY.loc[:,'year'][::2], showgrid=False),
                                               yaxis=go.layout.YAxis(  # hoverformat = '.1f'
                                               )
                                               , yaxis2=go.layout.YAxis(tickformat='.1%', gridwidth=3, showgrid=False,
                                                                        overlaying='y',
                                                                        side='right')
                                               , legend=dict(x=1.1, y=1)
                                               ))
    return fig.update_layout(template='plotly_dark',title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')

@app.callback(
    Output(component_id='output-graph-thuongY-2', component_property='figure'),
    [Input(component_id='intermediate-value-thuongY', component_property='children')]
)
def roae(dat):
    statsY = pd.read_json(dat, orient='split')
    test1 = go.Scatter(y=statsY.loc[:, 'roe'], x=statsY.loc[:, 'year'], name="roe", yaxis='y2',
                       line=dict(color='red', width=3), mode='lines+markers')
    test2 = go.Scatter(y=statsY.loc[:, 'roe_core'], x=statsY.loc[:, 'year'], name="roe_cốt lõi", yaxis='y2',
                       line=dict(color='rgb(191, 214, 48)', width=3), mode='lines+markers')
    test3 = go.Bar(y=statsY.loc[:, 'op'], x=statsY.loc[:, 'year'], name='LN cốt lõi',
                   marker=dict(color=('teal')))
    test4 = go.Bar(y=-statsY.loc[:, 'int_exp'], x=statsY.loc[:, 'year'], name='Chi phí lãi vay',
                   marker=dict(color=('goldenrod')))
    test5 = go.Bar(y=statsY.loc[:, 'fin_income'], x=statsY.loc[:, 'year'], name='LN tài chính',
                   marker=dict(color=('#A4DE02')))
    test6 = go.Bar(y=statsY.loc[:, 'jv_income'], x=statsY.loc[:, 'year'], name='LN LDLK',
                   marker=dict(color=('deeppink')))
    test7 = go.Bar(y=statsY.loc[:, 'other_income'], x=statsY.loc[:, 'year'], name='LN khác',
                   marker=dict(color=('darkgray')))
    test8 = go.Scatter(y=statsY.loc[:, 'net_income'], x=statsY.loc[:, 'year'], name="LNST",
                       line=dict(color='darkturquoise', width=3, dash='dot'), mode='lines')
    roae = [test1, test2, test3, test4, test5, test6,test7,test8]
    fig = go.Figure(data=roae, layout=go.Layout(barmode='relative',
                                                title='Lợi nhuận trước thuế',
                                                xaxis=dict(tickvals=statsY.loc[:,'year'][::2],),
                                                yaxis2=go.layout.YAxis(tickformat='.1%', gridwidth=3,
                                                                       overlaying='y',
                                                                       side='right',
                                                                       showgrid=False)

                                                , legend=dict(x=1.1, y=1)

                                                # yaxis2=dict(title='price-thuongY',overlaying='y', side='right')
                                                ))
    return fig.update_layout(template='plotly_dark',title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')

@app.callback(
    Output(component_id='output-graph-thuongY-3', component_property='figure'),
    [Input(component_id='intermediate-value-thuongY', component_property='children')]
)
def asset(dat):
    statsY = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsY.loc[:, "bs_cash"], x=statsY.loc[:, "year"], name='Tiền+ĐTNH',
                        marker=dict(color=('teal')))
    asset_bar2 = go.Bar(y=statsY.loc[:, "bs_ar"], x=statsY.loc[:, "year"], name="Phải thu ngắn hạn",
                        marker=dict(color=('#A4DE02')))
    asset_bar3 = go.Bar(y=statsY.loc[:, "net_inven"], x=statsY.loc[:, "year"], name="Hàng tồn kho",
                        marker=dict(color=('green')))
    asset_bar4 = go.Bar(y=statsY.loc[:, "bs_fa"], x=statsY.loc[:, "year"], name="TSCĐ",
                        marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar5 = go.Bar(y=statsY.loc[:, "cip"], x=statsY.loc[:, "year"], name="XDCB",
                        marker=dict(color=('goldenrod')))
    asset_bar6 = go.Bar(y=statsY.loc[:, "bs_jv"], x=statsY.loc[:, "year"], name="Công ty LDLK",
                        marker=dict(color=('deeppink')))
    asset_bar7 = go.Bar(y=statsY.loc[:, "other_asset"], x=statsY.loc[:, "year"], name="Khác",
                        marker=dict(color=('darkgray')))
    asset_bar8 = go.Scatter(y=statsY.loc[:, "ca/ta"], x=statsY.loc[:, "year"], yaxis='y2',
                            name="TS ngắn hạn/Tổng tài sản", line=dict(color='deeppink', width=3,dash='dot'),
                            mode='lines')
    asset_bar9 = go.Scatter(y=statsY.loc[:, "mc"], x=statsY.loc[:, "year"], yaxis='y', name="Vốn hóa",
                            line=dict(color='darkturquoise', width=3), mode='lines+markers')
    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4, asset_bar5, asset_bar6, asset_bar7,asset_bar8,asset_bar9]

    fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'
                                                      , xaxis=dict(tickvals=statsY.loc[:,'year'][::2],)
                                                      , yaxis=go.layout.YAxis(gridwidth=3)
                                                      , yaxis2=go.layout.YAxis(showgrid=False, tickformat='%',
                                                                               overlaying='y',
                                                                               side='right', range=[0, 1])
                                                      , title='Cơ cấu tài sản'
                                                      , legend=dict(x=1.1, y=1)
                                                      ))

    return fig.update_layout(template='plotly_dark',title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')

@app.callback(
    Output(component_id='output-graph-thuongY-4', component_property='figure'),
    [Input(component_id='intermediate-value-thuongY', component_property='children')]
)
def equity(dat):
    statsY = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsY.loc[:, "cap_e"], x=statsY.loc[:, "year"], name="Vốn điều lệ",
                        marker=dict(color=('teal')))
    asset_bar2 = go.Bar(y=statsY.loc[:, "re"], x=statsY.loc[:, "year"], name="LN chưa phân phối",
                        marker=dict(color=('#A4DE02')))
    asset_bar3 = go.Bar(y=statsY.loc[:, "bs_treasury"], x=statsY.loc[:, "year"],
                        name="Cổ phiếu quỹ", marker=dict(color=('pink')))
    asset_bar4 = go.Bar(y=statsY.loc[:, "other_equity"], x=statsY.loc[:, "year"],
                        name="Vốn khác", marker=dict(color=('green')))
    asset_bar5 = go.Bar(y=statsY.loc[:, "bs_ap"], x=statsY.loc[:, "year"], name="Phải trả ngắn hạn",
                        marker=dict(color=('#FFFF99')))
    asset_bar6 = go.Bar(y=statsY.loc[:, "st_debt"], x=statsY.loc[:, "year"], name='Vay ngắn hạn',
                        marker=dict(color=('goldenrod')))
    asset_bar7 = go.Bar(y=statsY.loc[:, "lt_debt"], x=statsY.loc[:, "year"], name="Vay dài hạn",
                        marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar8 = go.Bar(y=statsY.loc[:, "bs_cust_pre"], x=statsY.loc[:, "year"], name="KH trả tiền trước",
        marker=dict(color=('deeppink')))
    asset_bar10 = go.Bar(y=statsY.loc[:, "other_lia"], x=statsY.loc[:, "year"], name="Nợ khác",
                        marker=dict(color=('darkgray')))

    asset_bar9 = go.Scatter(y=statsY.loc[:, "mc"], x=statsY.loc[:, "year"], name="Vốn hóa",
                            line=dict(color='darkturquoise', width=3), mode='lines+markers')
    asset_bar11 = go.Scatter(y=statsY.loc[:, "DE"], x=statsY.loc[:, "year"], yaxis='y2', name="D/E",
                             line=dict(color='deeppink', width=3,dash='dot'), mode='lines')
    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4, asset_bar5, asset_bar6, asset_bar7, asset_bar8,
                   asset_bar9,asset_bar10,asset_bar11]

    fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'
                                                      , xaxis=dict(tickvals=statsY.loc[:,'year'][::2],)
                                                      , yaxis2=go.layout.YAxis(showgrid=False, tickformat='.1%',
                                                                               overlaying='y',
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
    Output(component_id='output-graph-thuongY-6', component_property='figure'),
    [Input(component_id='intermediate-value-thuongY', component_property='children')]
)
def cf(dat):
    statsY = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsY.loc[:, "net_income"], x=statsY.loc[:, "year"], name="LNST",
                        marker=dict(color=('teal')))
    asset_bar2 = go.Bar(y=statsY.loc[:, "cf_dep"], x=statsY.loc[:, "year"], name="Khấu hao",
                        marker=dict(color=('#A4DE02')))
    asset_bar3 = go.Bar(y=statsY.loc[:, "cf_e_raise"], x=statsY.loc[:, "year"], name="Tăng vốn",
                        marker=dict(color='deeppink'))
    asset_bar4 = go.Bar(y=statsY.loc[:, "div"], x=statsY.loc[:, "year"],
                        name="Cổ tức+CP quỹ", marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar5 = go.Bar(y=statsY.loc[:, "cf_capex"], x=statsY.loc[:, "year"], name="Đầu tư TSCĐ",
                        marker=dict(color=('#FFFF99')))
    asset_bar6 = go.Bar(y=statsY.loc[:, "cf_delta_debt"], x=statsY.loc[:, "year"], name="Vay thêm/trả",
                        marker=dict(color=('goldenrod')))
    asset_bar7 = go.Bar(y=statsY.loc[:, "cf_khac"], x=statsY.loc[:, "year"], name='CF khác',
                        marker=dict(color=('darkgray')))
    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4, asset_bar5, asset_bar6,asset_bar7]

    fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'
                                , xaxis=dict(tickvals=statsY.loc[:,'year'][::2])
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
    Output(component_id='output-graph-thuongY-5', component_property='figure'),
    [Input(component_id='intermediate-value-thuongY', component_property='children')]
)
def growth(dat):
    statsY = pd.read_json(dat, orient='split')
    g1 = go.Scatter(y=statsY.loc[:, "g_rev"], x=statsY.loc[:, "year"], name="Tăng trưởng doanh thu",
                    line=dict(color='teal', width=3), mode='lines+markers')
    g2 = go.Scatter(y=statsY.loc[:, "g_op"], x=statsY.loc[:, "year"], name="Tăng trưởng LN cốt lõi",
                    line=dict(color='rgb(191, 214, 48)', width=3), mode='lines+markers')
    g3 = go.Scatter(y=statsY.loc[:, "g_net_income"], x=statsY.loc[:, "year"], name="Tăng trưởng LNST",
                    line=dict(color='red', width=3), mode='lines+markers')
    g = [g1, g2, g3]
    fig = go.Figure(data=g, layout=go.Layout(barmode='relative'
                                                      , xaxis=dict(tickvals=statsY.loc[:,'year'][::2], showgrid=False)
                                                      , yaxis=go.layout.YAxis(showgrid=False, tickformat='.1%',
                                                                               overlaying='y',
                                                                               side='right')

                                                      , title='Tăng trưởng'
                                                      , legend=dict(x=1.1, y=1)
                                                      ))

    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')
@app.callback(
    Output(component_id='output-graph-thuongY-7', component_property='figure'),
    [Input(component_id='intermediate-value-thuongY', component_property='children')]
)
def pe(dat):
    statsY = pd.read_json(dat, orient='split')
    bar1 = go.Scatter(y=statsY.loc[:, "net_income"], x=statsY.loc[:, "year"], name='LNST',
                      line=dict(color='red', width=3,dash='dot'), mode='lines')
    bar2 = go.Scatter(y=statsY.loc[:, "core_e"], x=statsY.loc[:, "year"], name='LNST cốt lõi',
                      line=dict(color='rgb(191, 214, 48)', width=3,dash='dot'), mode='lines')
    bar3 = go.Scatter(y=statsY.loc[:, "mc"], x=statsY.loc[:, "year"], name="Vốn hóa (phải)",
                      line=dict(color='darkturquoise', width=3), mode='lines+markers')
    bar4 = go.Scatter(y=statsY.loc[:, "P/E"], x=statsY.loc[:, "year"], name="P/E (phải)",
                      line=dict(color='lavender', width=3), mode='lines', yaxis='y2')

    data_PE = [bar1, bar2, bar3,bar4]
    fig = go.Figure(data=data_PE, layout=go.Layout(xaxis=dict(tickvals=statsY.loc[:,'year'][::2],showgrid=False)
                                , yaxis=go.layout.YAxis(gridwidth=3)
                                , yaxis_type='log'
                                , yaxis2=go.layout.YAxis(overlaying='y', side='right', showgrid=False
                                                         ,rangemode='tozero')
                                , title='P/E'
                                , legend=dict(x=1.1, y=1)
                                ))

    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')


@app.callback(
    Output(component_id='output-graph-thuongY-8', component_property='figure'),
    [Input(component_id='intermediate-value-thuongY', component_property='children')]
)
def pb(dat):
    statsY = pd.read_json(dat, orient='split')
    bar1 = go.Scatter(y=statsY.loc[:, "te"], x=statsY.loc[:, "year"], name='Giá trị số sách',
                      line=dict(color='lavender', width=3), mode='lines+markers')
    bar2 = go.Scatter(y=statsY.loc[:, "mc"], x=statsY.loc[:, "year"], name='Vốn hóa',
                      line=dict(color='darkturquoise', width=3), mode='lines+markers')
    bar3 = go.Scatter(y=statsY.loc[:, "roe"], x=statsY.loc[:, "year"], name="ROE (phải)",
                      line=dict(color='red', width=3, dash='dot'), mode='lines', yaxis='y2')
    bar4 = go.Scatter(y=statsY.loc[:, "roe_core"], x=statsY.loc[:, "year"], name="ROE_core (phải)",
                      line=dict(color='rgb(191, 214, 48)', width=3, dash='dot'), mode='lines', yaxis='y2')
    # bar4 = go.Scatter(y=statsY.loc[:, "P/B"], x=statsY.loc[:, "year"], name="P/B (phải)",
    #                   line=dict(color='lavender', width=3,dash='dot'), mode='lines', yaxis='y2')

    data_PB = [bar1, bar2, bar3,bar4]

    fig = go.Figure(data=data_PB, layout=go.Layout(xaxis=dict(tickvals=statsY.loc[:,'year'][::2],showgrid=False)
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
