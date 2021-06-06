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

col = pd.read_excel('D:/Data/6.Python/project2/VND-col-ins.xlsx')
# col1 = ['gp', 'op', 'op1', 'EBT', 'pretax_inc', 'net_income', 'ni_parent', 'core_e']
# col3 = ['rev', 'gp', 'op', 'EBT', 'pretax_inc', 'net_income', 'ni_parent', 'core_e']
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

def get_dupsec(y):
    url = 'https://finfo-api.vndirect.com.vn/v3/stocks/financialStatement?secCodes=' + y + '&reportTypes=ANNUAL&modelTypes=411,412,413,414&fromDate=2000-12-31&toDate=2021-12-31'
    r = requests.get(url)
    raw = pd.json_normalize(json.loads(r.content)['data']['hits'])
    fs = raw[['_source.secCode', '_source.fiscalDate', '_source.itemName', '_source.numericValue',
            '_source.modelType']]
    fs.columns = ['ticker', 'dates', 'item', 'value', 'type']
    fs.loc[:, 'dates'] = pd.to_datetime(fs['dates'])
    fs.loc[:, 'year'] = fs['dates'].dt.year
    fs.loc[:, 'value'] = fs['value'].astype(float)
    fs = fs.set_index(['ticker','year','type'])
    fs = fs.pivot_table(index=['item','type'],values='value',columns='year')
    fs = fs.reset_index()
    fs=fs.set_index('item')
    return np.array(fs[fs.index.duplicated()].index)

dup = get_dupsec('BVH')

def get_insY(ticker):
    url = 'https://finfo-api.vndirect.com.vn/v3/stocks/financialStatement?secCodes=' + ticker + '&reportTypes=ANNUAL&modelTypes=1,2,3,89,90,91,92,101,102,103,104,411,412,413,414&fromDate=2000-12-31&toDate=2021-12-31'
    try:
        r = requests.get(url)
        raw = pd.json_normalize(json.loads(r.content)['data']['hits'])
        fs = raw[['_source.secCode', '_source.fiscalDate', '_source.itemName', '_source.numericValue',
                  '_source.modelType']]
        fs.columns = ['ticker', 'dates', 'item', 'value', 'type']
        fs.loc[:, 'dates'] = pd.to_datetime(fs['dates'])
        fs.loc[:, 'year'] = fs['dates'].dt.year
        fs.loc[:, 'value'] = fs['value'].astype(float)
        # fs.loc[(fs['type'] == 91) & (fs['item'] == 'Chi phí lãi vay') & (fs['year'] < 2015), 'item'] = 'Chi phí lãi vay2'
        fs = fs.drop(fs[(fs['item'].isin(dup) )&(fs['type'].isin([413,414]))].index)
        fs = fs.pivot_table(values='value', index=['ticker', 'year'], columns='item')
        fs = fs.rename(columns=dict(zip(col['item'], col['col'])))
#         del fs['drop']
        fs = fs.loc[:, fs.columns.notnull()]
        fs = fs.sort_index(level=[0,1])
        fs = fs.fillna(0)
        return fs
    except:
        print('Có lỗi, xin nhập mã khác')

def add_ratios(z):
    z['pl_math_reserve'] = np.abs(z['pl_math_reserve1'])+np.abs(z['pl_math_reserve2'])
    z['pl_taibaohiem_nhuong_rev'] = np.abs(z['pl_taibaohiem_nhuong_rev1'])+np.abs(z['pl_taibaohiem_nhuong_rev2'])
    z['pl_daodonglon']=z['pl_daodonglon1']+z['pl_daodonglon2']

    z['sel_exp'] = z['sel_exp1']+z['sel_exp2']+z['pl_baohiem_hoahong_exp']
    z['pl_baohiemgoc_inc'] = np.abs(z['pl_baohiemgoc_rev'])-np.abs(z['pl_baohiemgoc_exp'])
    z['pl_taibaohiem_inc'] = np.abs(z['pl_taibaohiem_rev']) - np.abs(z['pl_taibaohiem_exp'])
    z['pl_taibaohiem_nhuong_inc'] = np.abs(z['pl_taibaohiem_nhuong_rev1'])+np.abs(z['pl_taibaohiem_nhuong_rev2'])-np.abs(z['pl_taibaohiem_nhuong_exp'])
    z['pl_baohiem_rev'] = np.abs(z['pl_baohiemgoc_rev'])+np.abs(z['pl_taibaohiem_rev'])-np.abs(z['pl_taibaohiem_nhuong_exp'])
    z['pl_baohiem_exp'] = np.abs(z['pl_baohiemgoc_exp'])+np.abs(z['pl_taibaohiem_exp'])-np.abs(z['pl_taibaohiem_nhuong_rev1'])-np.abs(z['pl_taibaohiem_nhuong_rev2'])
    z['pl_baohiem_inc'] = z['pl_baohiem_rev']-z['pl_baohiem_exp']
    z['pl_baohiem_reserve'] = z['pl_math_reserve']+z['pl_delta_baohiem_boithuong_reserve']+z['pl_daodonglon']

    z['core_baohiem_inc'] = z['gross_rev']-z['pl_baohiem_reserve']-z['pl_baohiem_exp']
    z['core_baohiem_inc2'] = z['gp'] + z['sel_exp']
    z['core_inc'] = z['core_baohiem_inc']-z['admin_exp']-z['sel_exp']

    z['fin_inc'] = z['fin_rev']-z['fin_exp']
    z['jv_inc'] = z['jv_inc1']+z['jv_inc2']
    z['other_inc'] = z['pretax_inc']-z['core_inc']-z['fin_inc']-z['jv_inc']

    z['boithuong_baohiemgoc'] = np.abs(z['pl_baohiemgoc_exp'])/np.abs(z['pl_baohiemgoc_rev'])
    z['boithuong_taibaohiem'] = np.abs(z['pl_taibaohiem_exp']) / np.abs(z['pl_taibaohiem_rev'])
    z['boithuong_baohiem'] = z['pl_baohiem_exp']/z['pl_baohiem_rev']

    z['bs_quy'] = z['bs_quy1']+z['bs_quy2']
    z['lia_quyduphong'] = z['lia_quyduphong1']+z['lia_quyduphong2']
    z['htm_sec'] = z['st_htm_sec']+z['lt_htm_sec']
    z['other_asset'] = z['ta']-z['cce']-z['htm_sec']-z['st_ar']-z['asset_taibaohiem']-z['bs_jv']-z['st_inv']
    z['other_lia'] = z['tl']-z['st_debt']-z['lt_debt']-z['lia_bond_gov']-z['lia_quyduphong']
    z['other_equity'] = z['te']-z['cap_e']-z['re']-z['bs_quy']

    z['cf_tong'] = z['cfo'] + z['cfi'] + z['cff']
    z['other_cf'] = z['cf_tong'] - z['cf_div']  - z['cf_e_raise']
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
    x = get_insY(ticker)
    y = get_mc(ticker)
    x = x.reset_index()
    x = x.set_index(['ticker', 'year'])
    x = pd.merge(x, y, on=['ticker', 'year'], how='left')
    add_ratios(x)

    # for i in col3:
    #     g_func(x, i)
    add_stats(x)
    return x

layout = html.Div(children=[
    html.Header(children='Graph công ty bảo hiểm  Năm', className='ml-4',
                style={'font-size': '30px', 'font-weight': 'bold', 'font-family': 'Arial', 'text-align': 'center'}),
    html.Div(children='''Chọn mã CK và nhấn Enter:''', className='ml-4', style={'font-size': '20px'}),
    dcc.Input(id='input-ins-Y', value='BVH', type='text', debounce=True, className='ml-4'),
    html.Br(),
    html.Br(),
    dbc.Container(id='price-insY',className='six columns',
                 style={'width': '30%', 'display': 'inline-block','margin-left':'5px'}),
    html.Div(id='intermediate-value-insY', style={'display': 'none'}),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-insY-1')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-insY-2')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-insY-3')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-insY-4')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-insY-5')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-insY-6')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-insY-7')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-insY-8')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row')


])
@app.callback(Output('price-insY', 'children'),
              [Input(component_id='input-ins-Y', component_property='value')])

def display_price(ticker):
    price = get_price(ticker)
    mc = price['value']/1000000000
    text = 'Vốn hóa của {code} tại {date} là: {value} tỷ VND'.format(code=price['code'].values[0],date=price['reportDate'].values[0],value=str(mc.map('{:,.0f}'.format).values[0]))
    alert = dbc.Alert(text,dismissable=False,is_open=True,color="success")
    return alert

@app.callback(Output('intermediate-value-insY', 'children'), [Input(component_id='input-ins-Y', component_property='value')])
def clean_data(ticker):
    statsY = add_dfY(ticker)
    statsY = statsY.reset_index()
    statsY = statsY.set_index('ticker')
    return statsY.to_json(date_format='iso', orient='split')

@app.callback(
    Output(component_id='output-graph-insY-1', component_property='figure'),
    [Input(component_id='intermediate-value-insY', component_property='children')]
)
def profit(dat):
    statsY = pd.read_json(dat, orient='split')
    test1 = go.Bar(y=statsY.loc[:, "core_baohiem_inc"], x=statsY.loc[:, "year"], name='LN bảo hiểm (sau dự phòng)',
                   marker=dict(color=('teal')))
    test2 = go.Bar(y=statsY.loc[:, "fin_inc"], x=statsY.loc[:, "year"], name='LN tài chính',
                   marker=dict(color=('#A4DE02')))
    test3 = go.Bar(y=statsY.loc[:, "jv_inc"], x=statsY.loc[:, "year"], name='LN LDLK',
                   marker=dict(color=('yellow')))
    test4 = go.Bar(y=-statsY.loc[:, "sel_exp"], x=statsY.loc[:, "year"], name='Chi phí bán hàng',
                   marker=dict(color=('orange')))
    test5 = go.Bar(y=-statsY.loc[:, "admin_exp"], x=statsY.loc[:, "year"], name='Chi phí quản lý',
                   marker=dict(color=('deeppink')))
    test6 = go.Bar(y=statsY.loc[:, "other_inc"], x=statsY.loc[:, "year"], name='LN khác',
                   marker=dict(color=('darkgray')))

    test7 = go.Scatter(y=statsY.loc[:, "net_income"], x=statsY.loc[:, "year"],
                       name="LNST (phải)", line=dict(color='darkturquoise', width=4,dash='dot'),yaxis='y2',
                       mode='lines')

    data_set = [test1, test2, test3,test4,test5,test6,test7]

    fig = go.Figure(data=data_set,layout=go.Layout(barmode='relative',
                                title='Phân tích lợi nhuận trước thuế',
                                xaxis=dict(tickvals=statsY.loc[:,'year']),
                                yaxis2=go.layout.YAxis(gridwidth=3, overlaying='y', side='right',rangemode='tozero'
                                                                          , showgrid=False),

                                legend=dict(x=1.1, y=1)

                           ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')

@app.callback(
    Output(component_id='output-graph-insY-2', component_property='figure'),
    [Input(component_id='intermediate-value-insY', component_property='children')]
)


def roae(dat):
    statsY = pd.read_json(dat, orient='split')
    test1 = go.Bar(y=statsY.loc[:, "pl_baohiemgoc_inc"], x=statsY.loc[:, "year"], name='Thu nhập BH gốc',
                       marker=dict(color=('teal')))
    test2 = go.Bar(y=statsY.loc[:, "pl_taibaohiem_inc"], x=statsY.loc[:, "year"], name='Thu nhập tài BH',
                       marker=dict(color=('deeppink')))
    test3 = go.Bar(y=statsY.loc[:, "pl_taibaohiem_nhuong_inc"], x=statsY.loc[:, "year"], name='Thu nhập nhượng tái BH',
                       marker=dict(color=('lavender')))
    test5 = go.Scatter(y=statsY.loc[:, "core_baohiem_inc"], x=statsY.loc[:, "year"], name="Core bảo hiểm",
                       line=dict(color='darkturquoise', width=4, dash='dot'), mode='lines')
    test4 = go.Bar(y=-statsY.loc[:, "pl_baohiem_reserve"], x=statsY.loc[:, "year"], name='Dự phòng',
                   marker=dict(color=('orange')))
    test6 = go.Scatter(y=statsY.loc[:, "boithuong_baohiem"], x=statsY.loc[:, "year"],
                       name="Tỷ lệ bồi thường", line=dict(color='lavender', width=3), yaxis='y2',
                       mode='lines+markers')

    roae = [test1, test2, test3, test4, test5,test6]
    fig = go.Figure(data=roae, layout=go.Layout(barmode='relative',
                                title='Cơ cấu lợi nhuận bảo hiểm',
                                xaxis=dict(tickvals=statsY.loc[:,'year']),
                                legend=dict(x=1.1, y=1),
                                yaxis2=dict(overlaying='y2', side='right',showgrid=False,tickformat='.1%',rangemode='tozero')
                                ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')



@app.callback(
    Output(component_id='output-graph-insY-3', component_property='figure'),
    [Input(component_id='intermediate-value-insY', component_property='children')]
)
def asset(dat):
    statsY = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsY.loc[:, "cce"], x=statsY.loc[:, "year"], name='Tiền và TĐT',
                        marker=dict(color=('teal')))
    asset_bar2 = go.Bar(y=statsY.loc[:, "st_inv"], x=statsY.loc[:, "year"], name="Đầu tư ngắn hạn",
                        marker=dict(color=('green')))
    asset_bar3 = go.Bar(y=statsY.loc[:, "st_htm_sec"], x=statsY.loc[:, "year"], name="HTM ngắn hạn",
                        marker=dict(color=('#A4DE02')))
    asset_bar4 = go.Bar(y=statsY.loc[:, "lt_htm_sec"], x=statsY.loc[:, "year"], name="HTM dài hạn",
                        marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar5 = go.Bar(y=statsY.loc[:, "st_ar"], x=statsY.loc[:, "year"], name="Phải thu ngắn hạn",
                        marker=dict(color=('orange')))
    asset_bar6 = go.Bar(y=statsY.loc[:, "asset_taibaohiem"], x=statsY.loc[:, "year"], name="Tài sản tái bảo hiểm",
                        marker=dict(color=('deeppink')))
    asset_bar7 = go.Bar(y=statsY.loc[:, "bs_jv"], x=statsY.loc[:, "year"], name="LDLK",
                        marker=dict(color=('lavender')))
    asset_bar8 = go.Bar(y=statsY.loc[:, "other_asset"], x=statsY.loc[:, "year"], name="Khác",
                        marker=dict(color=('darkgray')))
    asset_bar9 = go.Scatter(y=statsY.loc[:, "mc"], x=statsY.loc[:, "year"], yaxis='y',
                            name="Vốn hóa", line=dict(color='darkturquoise', width=4),
                            mode='lines+markers')

    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4,
                  asset_bar5, asset_bar6, asset_bar7,asset_bar8,asset_bar9]


    fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'
                                , xaxis=dict(tickvals=statsY.loc[:,'year'])
                                , yaxis=go.layout.YAxis(gridwidth=3  # ,hoverformat = '.1f'
                                                        )
                                , yaxis2=go.layout.YAxis(showgrid=False, tickformat='.2%',
                                                         overlaying='y', side='right')
                                , title='Cơ cấu tài sản'
                                , legend=dict(x=1.1, y=1)
                                ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')



@app.callback(
    Output(component_id='output-graph-insY-4', component_property='figure'),
    [Input(component_id='intermediate-value-insY', component_property='children')]
)
def equity(dat):
    statsY = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsY.loc[:, "cap_e"], x=statsY.loc[:, "year"], name="Vốn điều lệ",
                        marker=dict(color=('green')))
    asset_bar2 = go.Bar(y=statsY.loc[:, "re"], x=statsY.loc[:, "year"], name="LN chưa phân phối",
                        marker=dict(color=('#A4DE02')))
    asset_bar3 = go.Bar(y=statsY.loc[:, "bs_quy"], x=statsY.loc[:, "year"], name="Quỹ thuộc VCSH")
    asset_bar4 = go.Bar(y=statsY.loc[:, "other_equity"], x=statsY.loc[:, "year"],
                        name="Vốn khác", marker=dict(color=('pink')))
    asset_bar5 = go.Bar(y=statsY.loc[:, "st_debt"], x=statsY.loc[:, "year"], name="Vay ngắn hạn",
                        marker=dict(color=('purple')))
    asset_bar6 = go.Bar(y=statsY.loc[:, "lt_debt"], x=statsY.loc[:, "year"], name='Vay dài hạn',
                        marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar7 = go.Bar(y=statsY.loc[:, "lia_bond_gov"], x=statsY.loc[:, "year"], name="Trái phiếu chính phủ",
                        marker=dict(color=('lavender')))
    asset_bar8 = go.Bar(y=statsY.loc[:, "lia_quyduphong"], x=statsY.loc[:, "year"], name="Dự phòng nghiệp vụ",
                        marker=dict(color=('orange')))
    asset_bar9 = go.Bar(y=statsY.loc[:, "other_lia"], x=statsY.loc[:, "year"], name="Nợ khác",
                        marker=dict(color=('darkgray')))
    asset_bar11 = go.Scatter(y=statsY.loc[:, "E/A"], x=statsY.loc[:, "year"], yaxis='y2', name="E/A",
                             line=dict(color='deeppink', width=3, dash='dot'), mode='lines')
    asset_bar10 = go.Scatter(y=statsY.loc[:, "mc"], x=statsY.loc[:, "year"], yaxis='y',name="Vốn hóa",
                            line=dict(color='darkturquoise', width=4), mode='lines+markers')

    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4, asset_bar5, asset_bar6, asset_bar7,
                  asset_bar8,asset_bar9,asset_bar10,asset_bar11]
    fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'
                                , xaxis=dict(tickvals=statsY.loc[:,'year'])
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

@app.callback(
    Output(component_id='output-graph-insY-5', component_property='figure'),
    [Input(component_id='intermediate-value-insY', component_property='children')]
)
def growth(dat):
    statsY = pd.read_json(dat, orient='split')
    asset_bar1 = go.Scatter(y=statsY.loc[:, "roe"], x=statsY.loc[:, "year"],name="ROE",
                            line=dict(color='darkturquoise', width=4), mode='lines+markers')
    asset_bar2 = go.Scatter(y=statsY.loc[:, "roa"], x=statsY.loc[:, "year"],name="ROA",
                            line=dict(color='orange', width=4), mode='lines+markers')
    asset_data = [asset_bar1, asset_bar2]
    fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'
                                , xaxis=dict(showgrid=False,tickvals=statsY.loc[:,'year'])
                                , yaxis2=go.layout.YAxis(showgrid=False, tickformat='.1%', title='D/A', overlaying='y',
                                                         side='right')
                                , yaxis=go.layout.YAxis(gridwidth=3,  tickformat='.1%'
                                                        )
                                , title='ROE'
                                , legend=dict(x=1.1, y=1)
                                ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')


@app.callback(
    Output(component_id='output-graph-insY-6', component_property='figure'),
    [Input(component_id='intermediate-value-insY', component_property='children')]
)
def cf(dat):
    statsY = pd.read_json(dat, orient='split')
    bar2 = go.Bar(y=statsY.loc[:, "cfo"], x=statsY.loc[:, "year"], name="Dòng tiền từ kinh doanh",
                        marker=dict(color=('teal')))
    bar3 = go.Bar(y=statsY.loc[:, "cfi"], x=statsY.loc[:, "year"], name="Dòng tiền từ đầu tư",
                  marker=dict(color=('orange')))
    bar1 = go.Bar(y=statsY.loc[:, "cf_div"], x=statsY.loc[:, "year"], name="Cổ tức tiền mặt",
                  marker=dict(color=('rgb(200, 0, 0)')))
    bar4 = go.Bar(y=statsY.loc[:, "cf_e_raise"], x=statsY.loc[:, "year"], name="Tăng vốn",
                  marker=dict(color=('deeppink')))

    bar5 = go.Bar(y=statsY.loc[:, "other_cf"], x=statsY.loc[:, "year"], name="CF khác",
                  marker=dict(color=('darkgray')))
    tong = go.Scatter(y=statsY.loc[:, "cf_tong"], x=statsY.loc[:, "year"],
                      name="Tổng dòng tiền (phải)", yaxis='y2', line=dict(color='darkturquoise', width=3),
                      mode='lines+markers')
    data_CF = [bar1, bar2, bar3, bar4, bar5, tong]
    fig = go.Figure(data = data_CF,
            layout = go.Layout(barmode='relative',
                                xaxis=dict(tickvals=statsY.loc[:, "year"])
                                , yaxis=go.layout.YAxis(gridwidth=3, rangemode='tozero')
                                , yaxis2= go.layout.YAxis(overlaying='y', side='right', showgrid=False, rangemode='tozero')
                                , title='Dòng tiền'
                                , legend=dict(x=1.1, y=1)
                                ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')


@app.callback(
    Output(component_id='output-graph-insY-7', component_property='figure'),
    [Input(component_id='intermediate-value-insY', component_property='children')]
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
    Output(component_id='output-graph-insY-8', component_property='figure'),
    [Input(component_id='intermediate-value-insY', component_property='children')]
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
