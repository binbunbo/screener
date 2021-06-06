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
import pathlib
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../assets/col").resolve()
col = pd.read_excel(DATA_PATH.joinpath("VND-col-bank.xlsx"))


col3 = ['net_income', 'ni_parent']
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
        df['ticker']=ticker
        df = df.sort_values('dates',ascending=True).groupby(['ticker','year','quarter'])[['mc']].apply(lambda x: x.iloc[-1])
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
def get_bankQ(ticker):
    url = 'https://finfo-api.vndirect.com.vn/v3/stocks/financialStatement?secCodes=' + ticker + '&reportTypes=QUARTER&modelTypes=1,2,3,89,90,91,101,102,103,104,411,412,413&fromDate=2000-12-31&toDate=2021-12-31'
    try:
        r = requests.get(url)
        raw = pd.json_normalize(json.loads(r.content)['data']['hits'])
        fs = raw[['_source.secCode', '_source.fiscalDate', '_source.itemName', '_source.numericValue',
                  '_source.modelType']]
        fs.columns = ['ticker', 'dates', 'item', 'value', 'type']
        fs.loc[:, 'dates'] = pd.to_datetime(fs['dates'])
        fs.loc[:, 'year'] = fs['dates'].dt.year
        fs.loc[:, 'quarter'] = fs['dates'].dt.quarter
        fs.loc[:, 'value'] = fs['value'].astype(float)
        fs = fs.drop(fs[(fs['item'].str.contains('kế toán trước thuế')) & (fs['type'] == 3)].index)
        fs = fs.pivot_table(values='value', index=['ticker', 'year','quarter','dates'], columns='item')
        fs = fs.rename(columns=dict(zip(col['item'], col['col'])))
        del fs['drop']
        fs = fs.sort_index(level=[0,1,2])
        return fs
    except:
        print('Có lỗi, xin nhập mã khác')

def ttm(x, i):
    x[i + "_4Q"] = x.groupby(level=[0])[i].apply(lambda x: x.rolling(4, min_periods=4).sum())
def add_ratios(x):
    x['dautu_inc'] = x['ck_inc'] + x['invest_ck_inc'] + x['equity_inc']
    x['interest_inc_core'] = x['interest_inc'] - x['provision_exp']
    x['net_asset_loan'] = x['gross_asset_loan'] + x['pro_asset_loan']
    # x['pretax_inc'] = x['interest_inc_core'] + x['fx_inc'] + x['dautu_inc'] + x['other_inc'] - x['admin_exp']
    x['earning_asset'] = x['net_asset_loan'] + x['asset_loan_tctd'] + x['asset_invest_ck']
    x['interest_bearing_lia'] = x['lia_deposit_cust'] + x['lia_tctd'] + x['lia_giaytocogia'] + x['lia_sbv']
    x['bs_cash'] = x['asset_cce'] + x['asset_tctd']

    x['other_asset'] = x['ta'] - x['bs_cash'] - x['asset_trading_ck'] - x['asset_invest_ck'] - x['asset_lt_inv'] - x[
        'bs_fa'] - x['net_asset_loan']
    x['other_lia'] = x['tl'] - x['lia_sbv'] - x['lia_deposit_cust'] - x['lia_tctd'] - x['lia_giaytocogia']
    x['other_equity'] = x['te'] - x['contributed_e'] - x['re'] - x['bs_treasury']

    x['asset_yield'] = x['interest_rev'] / x['earning_asset'].rolling(2).mean()
    x['cof'] = np.abs(x['interest_exp']) / x['interest_bearing_lia'].rolling(2).mean()
    x['nim'] = x['interest_inc'] / x['earning_asset'].rolling(2).mean()
    x['cir'] = x['admin_exp'] / (x['op_truocduphong']+x['admin_exp'])
    x['credit_cost'] = x['provision_exp'] / x['earning_asset'].rolling(2).mean()
    x['bad_debt'] = x['nhom3'] + x['nhom4'] + x['nhom5']
    x['problem_asset'] = x['bad_debt'] + x['nhom2'] + x['net_vamc']
    x['npl'] = x['bad_debt'] / x['gross_asset_loan']
    x['problem_asset_pct'] = x['problem_asset'] / x['gross_asset_loan']
    x['casa'] = x['lia_deposit_kokyhan'] / (x['lia_deposit_cust'] + x['lia_deposit_tctd'])
    x['E/A'] = x['te'] / x['ta']
#
#
# def g_func(x, i):
#     x["g_" + i] = x.sort_index(level=[0, 1]).groupby(level=[0])[i].diff(periods=1) / np.abs(
#         x[i].sort_index(level=[0, 1]).shift(1))
#
#
def add_stats(x):
    x['E/A'] = x['te'] / x['ta']
    x['roe_4Q'] = x['net_income_4Q'] / x['te'].groupby(level=[0]).apply(lambda x: x.rolling(4, min_periods=4).mean())
    x['roa_4Q'] = x['net_income_4Q'] / x['ta'].groupby(level=[0]).apply(lambda x: x.rolling(4, min_periods=4).mean())
    x['P/E'] = x['mc'] / x['net_income_4Q']
    x['P/B'] = x['mc'] / x['te']


def add_dfQ(ticker):
    ticker = ticker.upper()
    x = get_bankQ(ticker)
    y = get_mc(ticker)
    x = x.reset_index()
    x = x.set_index(['ticker', 'year', 'quarter'])
    x = pd.merge(x, y, on=['ticker', 'year', 'quarter'], how='left')
    add_ratios(x)
    # for i in col1:
    #     margin_func(x,i)
    for i in col3:
        ttm(x, i)
    add_stats(x)
    return x


layout = html.Div(children=[
    html.Header(children='Graph bank Quý', className='ml-4',
                style={'font-size': '30px', 'font-weight': 'bold', 'font-family': 'Arial', 'text-align': 'center'}),
    html.Div(children='''Chọn mã CK và nhấn Enter:''', className='ml-4', style={'font-size': '20px'}),
    dcc.Input(id='input-bankQ', value='VCB', type='text', debounce=True, className='ml-4'),
    html.Br(),
    html.Br(),
    dbc.Container(id='price-bankQ',className='six columns',
                 style={'width': '30%', 'display': 'inline-block','margin-left':'5px'}),
    html.Div(id='intermediate-value-bankQ', style={'display': 'none'}),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-bankQ-1')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-bankQ-2')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-bankQ-3')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-bankQ-4')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-bankQ-5')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-bankQ-6')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    # html.Div([
    #     html.Div([dcc.Graph(id='output-graph-bankQ-7')], className='six columns',
    #              style={'width': '50%', 'display': 'inline-block'}),
    #     html.Div([dcc.Graph(id='output-graph-bankQ-8')], className='six columns',
    #              style={'width': '50%', 'display': 'inline-block'}),
    # ], className='row')
])
@app.callback(Output('price-bankQ', 'children'),
              [Input(component_id='input-bankQ', component_property='value')])

def display_price(ticker):
    price = get_price(ticker)
    mc = price['value']/1000000000
    text = 'Vốn hóa của ' + price['code'].values[0] + ' tại ' + price['reportDate'].values[0] + ' là: ' + mc.map('{:,.0f}'.format).values[0] + ' tỷ VND'
    alert = dbc.Alert(text,dismissable=False,is_open=True,color="success")
    return alert

@app.callback(Output('intermediate-value-bankQ', 'children'), [Input(component_id='input-bankQ', component_property='value')])
def clean_data(ticker):
    statsQ = add_dfQ(ticker)
    statsQ = statsQ.reset_index()
    statsQ['dates'] = pd.PeriodIndex(year=statsQ.reset_index()["year"], quarter=statsQ.reset_index()["quarter"])
    statsQ['dates'] = statsQ['dates'].dt.to_timestamp(freq='Q')
    statsQ = statsQ.set_index('ticker')
    return statsQ.to_json(date_format='iso', orient='split')


@app.callback(
    Output(component_id='output-graph-bankQ-2', component_property='figure'),
    [Input(component_id='intermediate-value-bankQ', component_property='children')]
)
def profit(dat):
    statsQ = pd.read_json(dat, orient='split')
    test1 = go.Bar(y=statsQ.loc[:, "interest_rev"], x=statsQ.loc[:, "dates"], name='Doanh thu lãi vay',
                   marker=dict(color=('teal')))
    test2 = go.Bar(y=-np.abs(statsQ.loc[:, "interest_exp"]), x=statsQ.loc[:, "dates"], name='Chi phí lãi vay',
                   marker=dict(color=('rgb(200, 0, 0)')))
    test3 = go.Bar(y=-statsQ.loc[:, "provision_exp"], x=statsQ.loc[:, "dates"], name='Dự phòng tín dụng',
                   marker=dict(color='goldenrod'))
    test4 = go.Scatter(y=statsQ.loc[:, "asset_yield"], x=statsQ.loc[:, "dates"], name="Asset yield", yaxis='y2',
                      line=dict(color='rgb(191, 214, 48)', width=4,dash='dot'), mode='lines')
    test5 = go.Scatter(y=statsQ.loc[:, "cof"], x=statsQ.loc[:, "dates"], name="Cost of fund", yaxis='y2',
                       line=dict(color='blue', width=4,dash='dot'), mode='lines')
    test6 = go.Scatter(y=statsQ.loc[:, "nim"], x=statsQ.loc[:, "dates"], name="NIM", yaxis='y2',
                       line=dict(color='darkturquoise', width=4), mode='lines+markers')
    test7 = go.Scatter(y=statsQ.loc[:, "credit_cost"], x=statsQ.loc[:, "dates"], name="Trích lập",
                       yaxis='y2',
                       line=dict(color='green', width=4,dash='dot'), mode='lines')
    data_set = [test1, test2, test3,test4,test5,test6,test7]

    fig = go.Figure(data=data_set, layout=go.Layout(barmode='relative',
                                title='Phân tích lợi nhuận tín dụng',
                                yaxis2=go.layout.YAxis(tickformat='.1%', gridwidth=4, overlaying='y',
                                                       side='right',
                                                       showgrid=False),
                                legend=dict(x=1.1, y=1),
                                xaxis=dict(tickformat='%Y-%b', showgrid=False)
                           ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')



@app.callback(
    Output(component_id='output-graph-bankQ-1', component_property='figure'),
    [Input(component_id='intermediate-value-bankQ', component_property='children')]
)


def roae(dat):
    statsQ = pd.read_json(dat, orient='split')
    test1 = go.Bar(y=statsQ.loc[:, "interest_inc_core"], x=statsQ.loc[:, "dates"], name='Thu nhập lãi sau dự phòng',
                       marker=dict(color=('teal')))
    test2 = go.Bar(y=statsQ.loc[:, "service_inc"], x=statsQ.loc[:, "dates"], name='Thu nhập dịch vụ',
                       marker=dict(color=('#A4DE02')))
    test3 = go.Bar(y=statsQ.loc[:, "fx_inc"], x=statsQ.loc[:, "dates"], name='Thu nhập FX',
                       marker=dict(color=('peachpuff')))
    test4 = go.Bar(y=statsQ.loc[:, "dautu_inc"], x=statsQ.loc[:, "dates"], name='Thu nhập đầu tư',
                       marker=dict(color=('deeppink')))
    test5 = go.Bar(y=statsQ.loc[:, "other_inc"], x=statsQ.loc[:, "dates"], name='Thu nhập khác',
                       marker=dict(color=('darkgray')))
    test6 = go.Bar(y=-statsQ.loc[:, "admin_exp"], x=statsQ.loc[:, "dates"], name='Chi phí quản lý',
                   marker=dict(color=('goldenrod')))
    test7 = go.Scatter(y=statsQ.loc[:, "ni_parent"], x=statsQ.loc[:, "dates"],
                            name="LNST cty mẹ", line=dict(color='red', width=4),
                            mode='lines+markers')
    test8 = go.Scatter(y=statsQ.loc[:, "cir"], x=statsQ.loc[:, "dates"],
                            name="CIR", line=dict(color='darkturquoise', width=4,dash='dot'),
                            mode='lines',yaxis='y2')
    roae = [test1, test2, test3, test4, test5,test6,test7,test8]
    fig = go.Figure(data=roae, layout=go.Layout(barmode='relative',
                                title='Cơ cấu lợi nhuận trước thuế',
                                yaxis2=go.layout.YAxis(gridwidth=4, overlaying='y', side='right',
                                                       tickformat='.1%',showgrid=False),

                                legend=dict(x=1.1, y=1),
                                xaxis=dict(tickformat='%Y-%b', showgrid=False)
                                ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')



@app.callback(
    Output(component_id='output-graph-bankQ-3', component_property='figure'),
    [Input(component_id='intermediate-value-bankQ', component_property='children')]
)
def asset(dat):
    statsQ = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsQ.loc[:, "bs_cash"], x=statsQ.loc[:, "dates"], name='Tiền+ĐTNH',
                        marker=dict(color=('teal')))
    asset_bar2 = go.Bar(y=statsQ.loc[:, "asset_trading_ck"], x=statsQ.loc[:, "dates"], name="Chứng khoán KD",
                        marker=dict(color=('green')))
    asset_bar3 = go.Bar(y=statsQ.loc[:, "asset_invest_ck"], x=statsQ.loc[:, "dates"], name="Chứng khoán đầu tư",
                        marker=dict(color=('#A4DE02')))
    asset_bar4 = go.Bar(y=statsQ.loc[:, "net_asset_loan"], x=statsQ.loc[:, "dates"], name="Cho vay khách hàng",
                        marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar5 = go.Bar(y=statsQ.loc[:, "asset_lt_inv"], x=statsQ.loc[:, "dates"], name="Đầu tư dài hạn",
                        marker=dict(color=('orange')))
    asset_bar6 = go.Bar(y=statsQ.loc[:, "bs_fa"], x=statsQ.loc[:, "dates"], name="TSCĐ",
                        marker=dict(color=('deeppink')))
    asset_bar7 = go.Bar(y=statsQ.loc[:, "other_asset"], x=statsQ.loc[:, "dates"], name="Khác",
                        marker=dict(color=('darkgray')))
    asset_bar8 = go.Scatter(y=statsQ.loc[:, "mc"], x=statsQ.loc[:, "dates"], yaxis='y',
                            name="Vốn hóa", line=dict(color='darkturquoise', width=4),
                            mode='lines+markers')
    asset_bar9 = go.Scatter(y=statsQ.loc[:, "npl"], x=statsQ.loc[:, "dates"], yaxis='y2',
                            name="NPL", line=dict(color='red', width=3),
                            mode='lines')
    asset_bar10 = go.Scatter(y=statsQ.loc[:, "problem_asset_pct"], x=statsQ.loc[:, "dates"], yaxis='y2',
                            name="Problem asset (incl. VAMC)", line=dict(color='orange', width=3),
                            mode='lines')
    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4,
                  asset_bar5, asset_bar6, asset_bar7,
                  asset_bar8,asset_bar9, asset_bar10]

    fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'

                                , yaxis=go.layout.YAxis(gridwidth=4  # ,hoverformat = '.1f'
                                                        )
                                , yaxis2=go.layout.YAxis(showgrid=False, tickformat='.2%',
                                                         title='Nợ xấu', overlaying='y', side='right')
                                , title='Cơ cấu tài sản'
                                , legend=dict(x=1.1, y=1)
                                , xaxis=dict(tickformat='%Y-%b', showgrid=False)
                                ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')



@app.callback(
    Output(component_id='output-graph-bankQ-4', component_property='figure'),
    [Input(component_id='intermediate-value-bankQ', component_property='children')]
)
def equity(dat):
    statsQ = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsQ.loc[:, "contributed_e"], x=statsQ.loc[:, "dates"], name="Vốn điều lệ",
                        marker=dict(color=('green')))
    asset_bar2 = go.Bar(y=statsQ.loc[:, "re"], x=statsQ.loc[:, "dates"], name="LN chưa phân phối",
                        marker=dict(color=('#A4DE02')))
    asset_bar3 = go.Bar(y=statsQ.loc[:, "bs_treasury"], x=statsQ.loc[:, "dates"], name="Cổ phiếu quỹ")
    asset_bar4 = go.Bar(y=statsQ.loc[:, "other_equity"], x=statsQ.loc[:, "dates"],
                        name="Vốn khác", marker=dict(color=('pink')))
    asset_bar5 = go.Bar(y=statsQ.loc[:, "lia_sbv"], x=statsQ.loc[:, "dates"], name="Nợ chính phủ",
                        marker=dict(color=('yellow')))
    asset_bar6 = go.Bar(y=statsQ.loc[:, "lia_tctd"], x=statsQ.loc[:, "dates"], name='Nợ TCTD',
                        marker=dict(color=('orange')))
    asset_bar7 = go.Bar(y=statsQ.loc[:, "lia_deposit_cust"], x=statsQ.loc[:, "dates"], name="Tiền gửi KH",
                        marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar8 = go.Bar(y=statsQ.loc[:, "lia_giaytocogia"], x=statsQ.loc[:, "dates"], name="Giấy tờ có giá",
        marker=dict(color=('lavender')))
    asset_bar9 = go.Bar(y=statsQ.loc[:, "other_lia"], x=statsQ.loc[:, "dates"], name="Nợ khác",
                        marker=dict(color=('#CF6679')))
    asset_bar10 = go.Scatter(y=statsQ.loc[:, "mc"], x=statsQ.loc[:, "dates"], yaxis='y', name="Vốn hóa",
                             line=dict(color='darkturquoise', width=4), mode='lines+markers')
    asset_bar11 = go.Scatter(y=statsQ.loc[:, "casa"], x=statsQ.loc[:, "dates"], yaxis='y2',name="CASA",
                            line=dict(color='rgb(191, 214, 48)', width=3,dash='dot'), mode='lines')
    asset_bar12 = go.Scatter(y=statsQ.loc[:, "E/A"], x=statsQ.loc[:, "dates"], yaxis='y2', name="E/A",
                             line=dict(color='lavender', width=3,dash='dot'), mode='lines')
    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4, asset_bar5, asset_bar6, asset_bar7,
                  asset_bar8,asset_bar9,asset_bar10,asset_bar11,asset_bar12]
    fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'

                                , yaxis2=go.layout.YAxis(showgrid=False, tickformat='.1%', title='D/A',
                                                         overlaying='y',
                                                         side='right')
                                , yaxis=go.layout.YAxis(gridwidth=4  # ,hoverformat = '.1f'
                                                        )
                                , title='Cơ cấu nguồn vốn'
                                , legend=dict(x=1.1, y=1)
                                , xaxis=dict(tickformat='%Y-%b', showgrid=False)
                                ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')



@app.callback(
    Output(component_id='output-graph-bankQ-5', component_property='figure'),
    [Input(component_id='intermediate-value-bankQ', component_property='children')]
)
def pe(dat):
    statsQ = pd.read_json(dat, orient='split')
    bar1 = go.Scatter(y=statsQ.loc[:, "net_income_4Q"], x=statsQ.loc[:, "dates"], name='LNST 4Q',
                      line=dict(color='red', width=3,dash='dot'), mode='lines')
    bar2 = go.Scatter(y=statsQ.loc[:, "mc"], x=statsQ.loc[:, "dates"], name="Vốn hóa (phải)",
                      line=dict(color='darkturquoise', width=3), mode='lines+markers', yaxis='y')
    bar3 = go.Scatter(y=statsQ.loc[:, "P/E"], x=statsQ.loc[:, "dates"], name="P/E (phải)",
                      line=dict(color='lavender', width=3), mode='lines', yaxis='y2')

    data_PE = [bar1, bar2, bar3]
    fig = go.Figure(data=data_PE, layout=go.Layout(xaxis=dict(showgrid=False,tickformat='%Y-%b')
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
    Output(component_id='output-graph-bankQ-6', component_property='figure'),
    [Input(component_id='intermediate-value-bankQ', component_property='children')]
)
def pb(dat):
    statsQ = pd.read_json(dat, orient='split')
    bar1 = go.Scatter(y=statsQ.loc[:, "te"], x=statsQ.loc[:, "dates"], name='Giá trị số sách',
                      line=dict(color='lavender', width=3), mode='lines+markers')
    bar2 = go.Scatter(y=statsQ.loc[:, "mc"], x=statsQ.loc[:, "dates"], name='Vốn hóa',
                      line=dict(color='darkturquoise', width=3), mode='lines+markers')
    bar3 = go.Scatter(y=statsQ.loc[:, "roe_4Q"], x=statsQ.loc[:, "dates"], name="ROE (phải)",
                      line=dict(color='red', width=3,dash='dot'), mode='lines', yaxis='y2')

    # bar4 = go.Scatter(y=statsQ.loc[:, "P/B"], x=statsQ.loc[:, "dates"], name="P/B (phải)",
    #                   line=dict(color='lavender', width=3, dash='dot'), mode='lines', yaxis='y2')
    data_PB = [bar1, bar2, bar3]

    fig = go.Figure(data=data_PB, layout=go.Layout(xaxis=dict(showgrid=False,tickformat='%Y-%b')
                                                   , yaxis=go.layout.YAxis(gridwidth=3)
                                                   , yaxis_type='log'
                                                   , yaxis2=go.layout.YAxis(overlaying='y', side='right',rangemode='tozero',
                                                                            showgrid=False,tickformat='.1%')
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
