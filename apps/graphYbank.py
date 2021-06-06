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

col = pd.read_excel('D:/Data/6.Python/project2/VND-col-bank.xlsx')
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
def get_bankY(ticker):
    url = 'https://finfo-api.vndirect.com.vn/v3/stocks/financialStatement?secCodes=' + ticker + '&reportTypes=ANNUAL&modelTypes=1,2,3,89,90,91,101,102,103,104,411,412,413&fromDate=2000-12-31&toDate=2021-12-31'
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
        fs = fs.sort_index(level=[0,1])
        return fs
    except:
        print('Có lỗi, xin nhập mã khác')

# def margin_func(x, i):
#     x[i + "m"] = x[i] / x['rev']
#
def add_ratios(x):
    x['dautu_inc'] = x['ck_inc'] + x['invest_ck_inc'] + x['equity_inc']
    x['interest_inc_core'] = x['interest_inc'] - x['provision_exp']
    x['net_asset_loan'] = x['gross_asset_loan'] + x['pro_asset_loan']
    # x['pretax_inc'] = x['interest_inc_core'] + x['fx_inc'] + x['dautu_inc'] + x['other_inc']-x['admin_exp']
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
    x['credit_cost'] = x['provision_exp']/x['earning_asset'].rolling(2).mean()
    x['bad_debt'] = x['nhom3'] + x['nhom4'] + x['nhom5']
    x['problem_asset'] = x['bad_debt'] + x['nhom2'] + x['net_vamc']
    x['npl'] = x['bad_debt'] / x['gross_asset_loan']
    x['problem_asset_pct'] = x['problem_asset'] / x['gross_asset_loan']
    x['casa'] = x['lia_deposit_kokyhan'] / (x['lia_deposit_cust'] + x['lia_deposit_tctd'])
    x['E/A'] = x['te'] / x['ta']
    x['roe'] = x['ni_parent']/x['te'].rolling(2).mean()
    x['roa'] = x['ni_parent'] / x['ta'].rolling(2).mean()
#
#
def g_func(x, i):
    x["g_" + i] = x.sort_index(level=[0, 1]).groupby(level=[0])[i].diff(periods=1) / np.abs(
        x[i].sort_index(level=[0, 1]).shift(1))


def add_stats(x):
    x['E/A'] = x['te'] / x['ta']
    x['roe'] = x['net_income'] / x.sort_index(level=[0, 1])['te'].groupby(level=[0]).apply(
        lambda x: x.rolling(2, min_periods=2).mean())
    x['roa'] = x['net_income'] / x.sort_index(level=[0, 1])['ta'].groupby(level=[0]).apply(
        lambda x: x.rolling(2, min_periods=2).mean())
    x['P/E'] = x['mc']/x['net_income']
    x['P/B'] = x['mc'] / x['te']



def add_dfY(ticker):
    ticker = ticker.upper()
    x = get_bankY(ticker)
    y = get_mc(ticker)
    x = x.reset_index()
    x = x.set_index(['ticker', 'year'])
    x = pd.merge(x, y, on=['ticker', 'year'], how='left')
    add_ratios(x)
    # for i in col1:
    #     margin_func(x,i)
    for i in col3:
        g_func(x, i)
    add_stats(x)
    return x


layout = html.Div(children=[
    html.Header(children='Graph bank Năm', className='ml-4',
                style={'font-size': '30px', 'font-weight': 'bold', 'font-family': 'Arial', 'text-align': 'center'}),
    html.Div(children='''Chọn mã CK và nhấn Enter:''', className='ml-4', style={'font-size': '20px'}),
    dcc.Input(id='input-bank-Y', value='VCB', type='text', debounce=True, className='ml-4'),
    html.Br(),
    html.Br(),
    dbc.Container(id='price-bankY',className='six columns',
                 style={'width': '30%', 'display': 'inline-block','margin-left':'5px'}),
    html.Div(id='intermediate-value-bankY', style={'display': 'none'}),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-bankY-1')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-bankY-2')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-bankY-3')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-bankY-4')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-bankY-5')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-bankY-6')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    # html.Div([
    #     html.Div([dcc.Graph(id='output-graph-bankY-7')], className='six columns',
    #              style={'width': '50%', 'display': 'inline-block'}),
    #     html.Div([dcc.Graph(id='output-graph-bankY-8')], className='six columns',
    #              style={'width': '50%', 'display': 'inline-block'}),
    # ], className='row')
])
@app.callback(Output('price-bankY', 'children'),
              [Input(component_id='input-bank-Y', component_property='value')])

def display_price(ticker):
    price = get_price(ticker)
    mc = price['value']/1000000000
    text = 'Vốn hóa của {code} tại {date} là: {value} tỷ VND'.format(code=price['code'].values[0],date=price['reportDate'].values[0],value=str(mc.map('{:,.0f}'.format).values[0]))
    alert = dbc.Alert(text,dismissable=False,is_open=True,color="success")
    return alert

@app.callback(Output('intermediate-value-bankY', 'children'), [Input(component_id='input-bank-Y', component_property='value')])
def clean_data(ticker):
    statsY = add_dfY(ticker)
    statsY = statsY.reset_index()
    statsY = statsY.set_index('ticker')
    return statsY.to_json(date_format='iso', orient='split')


@app.callback(
    Output(component_id='output-graph-bankY-2', component_property='figure'),
    [Input(component_id='intermediate-value-bankY', component_property='children')]
)
def profit(dat):
    statsY = pd.read_json(dat, orient='split')
    test1 = go.Bar(y=statsY.loc[:, "interest_rev"], x=statsY.loc[:, "year"], name='Doanh thu lãi vay',
                   marker=dict(color=('teal')))
    test2 = go.Bar(y=-np.abs(statsY.loc[:, "interest_exp"]), x=statsY.loc[:, "year"], name='Chi phí lãi vay',
                   marker=dict(color=('rgb(200, 0, 0)')))
    test3 = go.Bar(y=-statsY.loc[:, "provision_exp"], x=statsY.loc[:, "year"], name='Dự phòng tín dụng',
                   marker=dict(color='goldenrod'))
    test4 = go.Scatter(y=statsY.loc[:, "asset_yield"], x=statsY.loc[:, "year"], name="Asset yield", yaxis='y2',
                      line=dict(color='rgb(191, 214, 48)', width=3,dash='dot'), mode='lines')
    test5 = go.Scatter(y=statsY.loc[:, "cof"], x=statsY.loc[:, "year"], name="Cost of fund", yaxis='y2',
                       line=dict(color='blue', width=3,dash='dot'), mode='lines')
    test6 = go.Scatter(y=statsY.loc[:, "nim"], x=statsY.loc[:, "year"], name="NIM", yaxis='y2',
                       line=dict(color='darkturquoise', width=3), mode='lines+markers')
    test7 = go.Scatter(y=statsY.loc[:, "credit_cost"], x=statsY.loc[:, "year"], name="Trích lập", yaxis='y2',
                       line=dict(color='green', width=3,dash='dot'), mode='lines')
    data_set = [test1, test2, test3,test4,test5,test6,test7]

    fig = go.Figure(data=data_set,layout=go.Layout(barmode='relative',
                                title='Phân tích lợi nhuận tín dụng', xaxis=dict(tickvals=statsY.loc[:,'year'][::2]),
                                yaxis2=go.layout.YAxis(tickformat='.1%', gridwidth=3, overlaying='y', side='right',
                                                       showgrid=False),
                                legend=dict(x=1.1, y=1)

                           ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')



@app.callback(
    Output(component_id='output-graph-bankY-1', component_property='figure'),
    [Input(component_id='intermediate-value-bankY', component_property='children')]
)


def roae(dat):
    statsY = pd.read_json(dat, orient='split')
    test1 = go.Bar(y=statsY.loc[:, "interest_inc_core"], x=statsY.loc[:, "year"], name='Thu nhập lãi sau dự phòng',
                       marker=dict(color=('teal')))
    test2 = go.Bar(y=statsY.loc[:, "service_inc"], x=statsY.loc[:, "year"], name='Thu nhập dịch vụ',
                       marker=dict(color=('#A4DE02')))
    test3 = go.Bar(y=statsY.loc[:, "fx_inc"], x=statsY.loc[:, "year"], name='Thu nhập FX',
                       marker=dict(color=('peachpuff')))
    test4 = go.Bar(y=statsY.loc[:, "dautu_inc"], x=statsY.loc[:, "year"], name='Thu nhập đầu tư',
                       marker=dict(color=('deeppink')))
    test5 = go.Bar(y=statsY.loc[:, "other_inc"], x=statsY.loc[:, "year"], name='Thu nhập khác',
                       marker=dict(color=('darkgray')))
    test6 = go.Bar(y=-statsY.loc[:, "admin_exp"], x=statsY.loc[:, "year"], name='Chi phí quản lý',
                   marker=dict(color=('goldenrod')))
    test7 = go.Scatter(y=statsY.loc[:, "ni_parent"], x=statsY.loc[:, "year"],
                            name="LNST cty mẹ", line=dict(color='red', width=3),
                            mode='lines+markers')
    test8 = go.Scatter(y=statsY.loc[:, "cir"], x=statsY.loc[:, "year"],
                       name="Cost to income", line=dict(color='darkturquoise', width=3,dash='dot'),yaxis='y2',
                       mode='lines')
    roae = [test1, test2, test3, test4, test5,test6,test7,test8]
    fig = go.Figure(data=roae, layout=go.Layout(barmode='relative',
                                title='Cơ cấu lợi nhuận trước thuế', xaxis=dict(tickvals=statsY.loc[:,'year'][::2]),
                                yaxis2=go.layout.YAxis(gridwidth=3, overlaying='y', side='right'
                                                       ,tickformat='.1%',showgrid=False),

                                legend=dict(x=1.1, y=1)
                                # yaxis2=dict(title='Price',overlaying='y', side='right')
                                ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')



@app.callback(
    Output(component_id='output-graph-bankY-3', component_property='figure'),
    [Input(component_id='intermediate-value-bankY', component_property='children')]
)
def asset(dat):
    statsY = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsY.loc[:, "bs_cash"], x=statsY.loc[:, "year"], name='Tiền+ĐTNH',
                        marker=dict(color=('teal')))
    asset_bar2 = go.Bar(y=statsY.loc[:, "asset_trading_ck"], x=statsY.loc[:, "year"], name="Chứng khoán KD",
                        marker=dict(color=('green')))
    asset_bar3 = go.Bar(y=statsY.loc[:, "asset_invest_ck"], x=statsY.loc[:, "year"], name="Chứng khoán đầu tư",
                        marker=dict(color=('#A4DE02')))
    asset_bar4 = go.Bar(y=statsY.loc[:, "net_asset_loan"], x=statsY.loc[:, "year"], name="Cho vay khách hàng",
                        marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar5 = go.Bar(y=statsY.loc[:, "asset_lt_inv"], x=statsY.loc[:, "year"], name="Đầu tư dài hạn",
                        marker=dict(color=('orange')))
    asset_bar6 = go.Bar(y=statsY.loc[:, "bs_fa"], x=statsY.loc[:, "year"], name="TSCĐ",
                        marker=dict(color=('deeppink')))
    asset_bar7 = go.Bar(y=statsY.loc[:, "other_asset"], x=statsY.loc[:, "year"], name="Khác",
                        marker=dict(color=('darkgray')))
    asset_bar8 = go.Scatter(y=statsY.loc[:, "mc"], x=statsY.loc[:, "year"], yaxis='y',
                            name="Vốn hóa", line=dict(color='darkturquoise', width=4),
                            mode='lines+markers')
    asset_bar9 = go.Scatter(y=statsY.loc[:, "npl"], x=statsY.loc[:, "year"], yaxis='y2',
                            name="NPL", line=dict(color='red', width=3),
                            mode='lines')
    asset_bar10 = go.Scatter(y=statsY.loc[:, "problem_asset_pct"], x=statsY.loc[:, "year"], yaxis='y2',
                            name="Problem asset (incl. VAMC)", line=dict(color='deeppink', width=3),
                            mode='lines')
    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4,
                  asset_bar5, asset_bar6, asset_bar7,
                  asset_bar8,asset_bar9, asset_bar10]

    fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'
                                , xaxis=dict(tickvals=statsY.loc[:,'year'][::2])
                                , yaxis=go.layout.YAxis(gridwidth=3  # ,hoverformat = '.1f'
                                                        )
                                , yaxis2=go.layout.YAxis(showgrid=False, tickformat='.2%',
                                                         title='Nợ xấu', overlaying='y', side='right')
                                , title='Cơ cấu tài sản'
                                , legend=dict(x=1.1, y=1)
                                ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')



@app.callback(
    Output(component_id='output-graph-bankY-4', component_property='figure'),
    [Input(component_id='intermediate-value-bankY', component_property='children')]
)
def equity(dat):
    statsY = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsY.loc[:, "contributed_e"], x=statsY.loc[:, "year"], name="Vốn điều lệ",
                        marker=dict(color=('green')))
    asset_bar2 = go.Bar(y=statsY.loc[:, "re"], x=statsY.loc[:, "year"], name="LN chưa phân phối",
                        marker=dict(color=('#A4DE02')))
    asset_bar3 = go.Bar(y=statsY.loc[:, "bs_treasury"], x=statsY.loc[:, "year"], name="Cổ phiếu quỹ")
    asset_bar4 = go.Bar(y=statsY.loc[:, "other_equity"], x=statsY.loc[:, "year"],
                        name="Vốn khác", marker=dict(color=('pink')))
    asset_bar5 = go.Bar(y=statsY.loc[:, "lia_sbv"], x=statsY.loc[:, "year"], name="Nợ chính phủ",
                        marker=dict(color=('yellow')))
    asset_bar6 = go.Bar(y=statsY.loc[:, "lia_tctd"], x=statsY.loc[:, "year"], name='Nợ TCTD',
                        marker=dict(color=('orange')))
    asset_bar7 = go.Bar(y=statsY.loc[:, "lia_deposit_cust"], x=statsY.loc[:, "year"], name="Tiền gửi KH",
                        marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar8 = go.Bar(y=statsY.loc[:, "lia_giaytocogia"], x=statsY.loc[:, "year"], name="Giấy tờ có giá",
        marker=dict(color=('lavender')))
    asset_bar9 = go.Bar(y=statsY.loc[:, "other_lia"], x=statsY.loc[:, "year"], name="Nợ khác",
                        marker=dict(color=('#CF6679')))
    asset_bar10 = go.Scatter(y=statsY.loc[:, "mc"], x=statsY.loc[:, "year"], yaxis='y', name="Vốn hóa",
                             line=dict(color='darkturquoise', width=4), mode='lines+markers')
    asset_bar11 = go.Scatter(y=statsY.loc[:, "casa"], x=statsY.loc[:, "year"], yaxis='y2',name="CASA",
                            line=dict(color='rgb(191, 214, 48)', width=3,dash='dot'), mode='lines')
    asset_bar12 = go.Scatter(y=statsY.loc[:, "E/A"], x=statsY.loc[:, "year"], yaxis='y2', name="E/A",
                             line=dict(color='lavender', width=3,dash='dot'), mode='lines')
    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4, asset_bar5, asset_bar6, asset_bar7,
                  asset_bar8,asset_bar9,asset_bar10,asset_bar11,asset_bar12]
    fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'
                                , xaxis=dict(tickvals=statsY.loc[:,'year'][::2])
                                , yaxis2=go.layout.YAxis(showgrid=False, tickformat='.1%', title='D/A', overlaying='y',
                                                         side='right')
                                , yaxis=go.layout.YAxis(gridwidth=4  # ,hoverformat = '.1f'
                                                        )
                                , title='Cơ cấu nguồn vốn'
                                , legend=dict(x=1.1, y=1)
                                ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')



# @app.callback(
#     Output(component_id='output-graph-bankY-5', component_property='figure'),
#     [Input(component_id='intermediate-value-bankY', component_property='children')]
# )
# def growth(dat):
#     statsY = pd.read_json(dat, orient='split')
#     asset_bar1 = go.Scatter(y=statsY.loc[:, "roe"], x=statsY.loc[:, "year"],name="ROE",
#                             line=dict(color='darkturquoise', width=4), mode='lines+markers')
#     asset_bar2 = go.Scatter(y=statsY.loc[:, "roa"], x=statsY.loc[:, "year"],name="ROA",
#                             line=dict(color='orange', width=4), mode='lines+markers')
#     asset_data = [asset_bar1, asset_bar2]
#     fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'
#                                 , xaxis=dict(tickvals=statsY.loc[:,'year'][::2])
#                                 , yaxis2=go.layout.YAxis(showgrid=False, tickformat='.1%', title='D/A', overlaying='y',
#                                                          side='right')
#                                 , yaxis=go.layout.YAxis(gridwidth=3,  tickformat='.1%'
#                                                         )
#                                 , title='ROE'
#                                 , legend=dict(x=1.1, y=1)
#                                 ))
#     return fig.update_layout(template='plotly_dark', title_x=0.5,
#                              plot_bgcolor='rgba(0, 0, 0, 0)',
#                              paper_bgcolor='rgba(0, 0, 0, 0)')


@app.callback(
    Output(component_id='output-graph-bankY-5', component_property='figure'),
    [Input(component_id='intermediate-value-bankY', component_property='children')]
)
def pe(dat):
    statsY = pd.read_json(dat, orient='split')
    bar1 = go.Scatter(y=statsY.loc[:, "net_income"], x=statsY.loc[:, "year"], name='LNST',
                      line=dict(color='red', width=3,dash='dot'), mode='lines')
    bar2 = go.Scatter(y=statsY.loc[:, "mc"], x=statsY.loc[:, "year"], name="Vốn hóa (phải)",
                      line=dict(color='darkturquoise', width=3), mode='lines+markers')
    bar3= go.Scatter(y=statsY.loc[:, "P/E"], x=statsY.loc[:, "year"], name="P/E (phải)",
                      line=dict(color='lavender', width=3), mode='lines', yaxis='y2')

    data_PE = [bar1, bar2, bar3]
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
    Output(component_id='output-graph-bankY-6', component_property='figure'),
    [Input(component_id='intermediate-value-bankY', component_property='children')]
)
def pb(dat):
    statsY = pd.read_json(dat, orient='split')
    bar1 = go.Scatter(y=statsY.loc[:, "te"], x=statsY.loc[:, "year"], name='Giá trị số sách',
                      line=dict(color='lavender', width=3), mode='lines+markers')
    bar2 = go.Scatter(y=statsY.loc[:, "mc"], x=statsY.loc[:, "year"], name='Vốn hóa',
                      line=dict(color='darkturquoise', width=3), mode='lines+markers')
    bar3 = go.Scatter(y=statsY.loc[:, "roe"], x=statsY.loc[:, "year"], name="ROE (phải)",
                      line=dict(color='red', width=3, dash='dot'), mode='lines', yaxis='y2')

    # bar4 = go.Scatter(y=statsY.loc[:, "P/B"], x=statsY.loc[:, "year"], name="P/B (phải)",
    #                   line=dict(color='lavender', width=3,dash='dot'), mode='lines', yaxis='y2')

    data_PB = [bar1, bar2, bar3]

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
