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
col = pd.read_excel(DATA_PATH.joinpath("VND-col-sec.xlsx"))


# col1 = ['gp', 'op', 'op1', 'EBT', 'pretax_inc', 'net_income', 'ni_parent', 'core_e']
col3 = ['net_income', 'ni_parent', 'core_inc','pretax_inc']

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
        print('C?? l???i, xin nh???p m?? kh??c')
        
def get_dupsec(y):
    url = 'https://finfo-api.vndirect.com.vn/v3/stocks/financialStatement?secCodes=' + y + '&reportTypes=ANNUAL&modelTypes=1,2,3,89,90,91,92,101,102,103,104,411,412,413,414&fromDate=2000-12-31&toDate=2021-12-31'
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
dup = get_dupsec('SSI')

def get_secQ(ticker):
    url = 'https://finfo-api.vndirect.com.vn/v3/stocks/financialStatement?secCodes=' + ticker + '&reportTypes=QUARTER&modelTypes=89,90,91,92&fromDate=2000-12-31&toDate=2021-12-31'
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
        fs.loc[
            (fs['type'] == 91) & (fs['item'] == 'Chi ph?? l??i vay') & (fs['year'] < 2015), 'item'] = 'Chi ph?? l??i vay2'
        fs = fs.drop(fs[(fs['item'].isin(dup)) & (fs['type'].isin([91, 92]))].index)
        fs = fs.pivot_table(values='value', index=['ticker', 'year','quarter','dates'], columns='item')
        fs = fs.rename(columns=dict(zip(col['item'], col['col'])))
        #         del fs['drop']
        fs = fs.loc[:, fs.columns.notnull()]
        fs = fs.sort_index(level=[0, 1,2])
        fs = fs.fillna(0)
        return fs
    except:
        print('C?? l???i, xin nh???p m?? kh??c')

def add_ratios(z):
    z['int_exp'] = np.abs(z['int_exp1'])
    z['baolanh_inc'] = z['baolanh_rev'] - np.abs(z['baolanh_exp'])
    z['tuvantaichinh_inc'] = z['tuvantaichinh_rev']-np.abs(z['tuvantaichinh_exp'])
    z['tuvandautu_inc'] = z['tuvandautu_rev']-np.abs(z['tuvandautu_exp'])
    z['luuky_inc'] = z['luuky_rev']-np.abs(z['luuky_exp'])
    z['margin_inc'] = z['margin_rev1']+z['other_rev']-np.abs(z['margin_exp'])
    z['fin_inc'] =  z['fin_rev']+z['htm_rev'] - (np.abs(z['fin_exp']-np.abs(z['int_exp'])))
    z['broker_inc'] = z['broker_rev']-np.abs(z['broker_exp'])
    z['tudoanh_realized_inc'] = z['fvtpl_realized_rev']+z['fvtpl_div']-np.abs(z['fvtpl_realized_exp'])-np.abs(z['tudoanh_exp'])+z['tudoanh_rev']
    z['tudoanh_unrealized_inc'] = (z['fvtpl_rev']-np.abs(z['fvtpl_exp']))-(z['tudoanh_realized_inc'])
    z['tudoanh_inc'] = z['tudoanh_realized_inc']+z['tudoanh_unrealized_inc']
    z['service_inc'] = z['baolanh_inc']+z['tuvantaichinh_inc']+z['tuvandautu_inc']+z['luuky_inc']
    z['core_inc'] = z['margin_inc']+z['broker_inc']+z['service_inc']-np.abs(z['admin_exp'])
    z['other_inc'] = (z['pretax_inc']+z['admin_exp'])-(z['service_inc']+z['broker_inc']+z['margin_inc']+z['tudoanh_inc']+z['fin_inc']-np.abs(z['int_exp']))
    z['other_inc2'] = z['pretax_inc']-(z['core_inc']+z['tudoanh_inc']+z['fin_inc']-np.abs(z['int_exp']))

    z['lia_bond'] = z['st_bond']+z['lt_bond']
    z['quy_duphong'] = z['quy_duphong1']+z['quy_duphong2']
    z['bs_htm'] = z['bs_st_htm']+z['bs_lt_htm']
    z['bs_margin'] = z['bs_margin1']+z['bs_margin2']
    z['other_asset'] = z['ta']-z['cce']-z['bs_st_fvtpl']-z['bs_afs']-z['bs_htm']-z['bs_jv']-z['bs_margin']
    z['other_lia'] = z['tl']-z['st_debt']-z['lt_debt']-z['lia_bond']
    z['debt'] = z['st_debt']+z['lt_debt']+z['lia_bond']
    z['other_equity'] = z['te']-z['cap_e']-z['re']-z['quy_duphong']
    z['cf_tong'] = z['cfo']+z['cfi']+z['cff']
    z['other_cf'] = z['cf_tong'] - z['cf_div'] - z['cf_treasury'] - z['cf_e_raise']
    
def ttm(x, i):
    x[i + "_4Q"] = x.groupby(level=[0])[i].apply(lambda x: x.rolling(4, min_periods=4).sum())
    
def add_stats(x):
    x['E/A'] = x['te'] / x['ta']
    x['margin/E'] = x['bs_margin']/x['te']
    x['cof'] = x['int_exp']/x.sort_index(level=[0, 1])['debt'].groupby(level=[0]).apply(
        lambda x: x.rolling(2, min_periods=2).mean())
    x['margin_yield'] = (x['margin_rev1']+x['other_rev']) / x.sort_index(level=[0, 1])['bs_margin'].groupby(level=[0]).apply(
        lambda x: x.rolling(2, min_periods=2).mean())
    x['tax_rate_4Q'] = 1 - x['net_income_4Q'] / x['pretax_inc_4Q']
    x['roe_4Q'] = x['net_income_4Q'] / x['te'].groupby(level=[0]).apply(lambda x: x.rolling(4, min_periods=4).mean())
    x['roa_4Q'] = x['net_income_4Q'] / x['ta'].groupby(level=[0]).apply(lambda x: x.rolling(4, min_periods=4).mean())
    x['P/E'] = x['mc']/x['net_income_4Q']
    x['P/B'] = x['mc']/x['te']
def add_dfQ(ticker):
    ticker = ticker.upper()
    x = get_secQ(ticker)
    y = get_mc(ticker)
    x = x.reset_index()
    x = x.set_index(['ticker', 'year', 'quarter'])
    x = pd.merge(y, x, on=['ticker', 'year', 'quarter'], how='left')
    add_ratios(x)
    for i in col3:
        ttm(x, i)
    # for i in col3:
    #     g_func(x, i)
    add_stats(x)
    return x


layout = html.Div(children=[
    html.Header(children='Graph c??ng ty ch???ng kho??n Qu??', className='ml-4',
                style={'font-size': '30px', 'font-weight': 'bold', 'font-family': 'Arial', 'text-align': 'center'}),
    html.Div(children='''Ch???n m?? CK v?? nh???n Enter:''', className='ml-4', style={'font-size': '20px'}),
    dcc.Input(id='input-sec-Q', value='SSI', type='text', debounce=True, className='ml-4'),
    html.Br(),
    html.Br(),
    dbc.Container(id='price-secQ',className='six columns',
                 style={'width': '30%', 'display': 'inline-block','margin-left':'5px'}),
    html.Div(id='intermediate-value-secQ', style={'display': 'none'}),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-secQ-1')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-secQ-2')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-secQ-3')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-secQ-4')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-secQ-5')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-secQ-6')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph-secQ-7')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph-secQ-8')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row')
])
@app.callback(Output('price-secQ', 'children'),
              [Input(component_id='input-sec-Q', component_property='value')])

def display_price(ticker):
    price = get_price(ticker)
    mc = price['value']/1000000000
    text = 'V???n h??a c???a ' + price['code'].values[0] + ' t???i ' + price['reportDate'].values[0] + ' l??: ' + mc.map('{:,.0f}'.format).values[0] + ' t??? VND'
    alert = dbc.Alert(text,dismissable=False,is_open=True,color="success")
    return alert

@app.callback(Output('intermediate-value-secQ', 'children'), [Input(component_id='input-sec-Q', component_property='value')])
def clean_data(ticker):
    statsQ = add_dfQ(ticker)
    statsQ = statsQ.reset_index()
    statsQ = statsQ.set_index('ticker')
    return statsQ.to_json(date_format='iso', orient='split')


@app.callback(
    Output(component_id='output-graph-secQ-2', component_property='figure'),
    [Input(component_id='intermediate-value-secQ', component_property='children')]
)
def profit(dat):
    statsQ = pd.read_json(dat, orient='split')
    test1 = go.Bar(y=statsQ.loc[:, "broker_inc"], x=statsQ.loc[:, "dates"], name='LN m??i gi???i',
                   marker=dict(color=('teal')))
    test2 = go.Bar(y=statsQ.loc[:, "margin_inc"], x=statsQ.loc[:, "dates"], name='LN margin',
                   marker=dict(color=('#A4DE02')))
    test3 = go.Bar(y=statsQ.loc[:, "service_inc"], x=statsQ.loc[:, "dates"], name='LN d???ch v???',
                   marker=dict(color=('rgb(200, 0, 0)')))
    test4 = go.Bar(y=statsQ.loc[:, "tudoanh_unrealized_inc"], x=statsQ.loc[:, "dates"],
                   name='LN t??? doanh ch??a th???c hi???n',
                   marker=dict(color=('deeppink')))
    test5 = go.Bar(y=statsQ.loc[:, "tudoanh_realized_inc"], x=statsQ.loc[:, "dates"], name='LN t??? doanh ???? th???c hi???n',
                   marker=dict(color=('purple')))
    test6 = go.Bar(y=statsQ.loc[:, "fin_inc"], x=statsQ.loc[:, "dates"], name='L???i nhu???n t??i ch??nh',
                   marker=dict(color='lavender'))
    test7 = go.Bar(y=statsQ.loc[:, "other_inc"], x=statsQ.loc[:, "dates"], name='L???i nhu???n kh??c',
                   marker=dict(color='darkgray'))
    test8 = go.Bar(y=-statsQ.loc[:, "admin_exp"], x=statsQ.loc[:, "dates"], name='Chi ph?? qu???n l??',
                   marker=dict(color='orange'))
    test9 = go.Scatter(y=statsQ.loc[:, "margin_yield"], x=statsQ.loc[:, "dates"],
                       name="Margin yield", line=dict(color='darkturquoise', width=3, dash='dot'), yaxis='y2',
                       mode='lines')
    test10 = go.Scatter(y=statsQ.loc[:, "cof"], x=statsQ.loc[:, "dates"],
                        name="Cost of fund", line=dict(color='red', width=3, dash='dot'), yaxis='y2',
                        mode='lines')

    data_set = [test1, test2, test3, test4, test5, test6, test7, test8, test9, test10]

    fig = go.Figure(data=data_set, layout=go.Layout(barmode='relative',
                                                    title='Ph??n t??ch l???i nhu???n tr?????c thu???',
                                                    xaxis=dict(tickformat='%Y-%b'),
                                                    yaxis2=go.layout.YAxis(gridwidth=3, overlaying='y', side='right'
                                                                           , tickformat='.1%', showgrid=False),

                                                    legend=dict(x=1.1, y=1)

                                                    ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')


@app.callback(
    Output(component_id='output-graph-secQ-1', component_property='figure'),
    [Input(component_id='intermediate-value-secQ', component_property='children')]
)

def roae(dat):
    statsQ = pd.read_json(dat, orient='split')
    test1 = go.Bar(y=statsQ.loc[:, "core_inc"], x=statsQ.loc[:, "dates"], name='Thu nh???p l??i ch???ng kho??n',
                       marker=dict(color=('teal')))
    test2 = go.Bar(y=statsQ.loc[:, "tudoanh_inc"], x=statsQ.loc[:, "dates"], name='Thu nh???p t??? doanh',
                       marker=dict(color=('deeppink')))
    test3 = go.Bar(y=statsQ.loc[:, "fin_inc"], x=statsQ.loc[:, "dates"], name='Thu nh???p t??i ch??nh',
                       marker=dict(color=('lavender')))
    test4 = go.Bar(y=statsQ.loc[:, "other_inc2"], x=statsQ.loc[:, "dates"], name='Thu nh???p kh??c',
                       marker=dict(color=('darkgray')))
    test5 = go.Bar(y=-np.abs(statsQ.loc[:, "int_exp"]), x=statsQ.loc[:, "dates"], name='Chi ph?? l??i vay',
                       marker=dict(color=('orange')))
    test6 = go.Scatter(y=statsQ.loc[:, "net_income"], x=statsQ.loc[:, "dates"], name="L???i nhu???n sau thu???",
                       line=dict(color='darkturquoise', width=4, dash='dot'), mode='lines')


    roae = [test1, test2, test3, test4, test5,test6]
    fig = go.Figure(data=roae, layout=go.Layout(barmode='relative',
                                title='C?? c???u l???i nhu???n tr?????c thu???',
                                xaxis=dict(tickformat='%Y-%b'),
                                legend=dict(x=1.1, y=1)
                                # yaxis2=dict(title='Price',overlaying='y', side='right')
                                ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')

@app.callback(
    Output(component_id='output-graph-secQ-3', component_property='figure'),
    [Input(component_id='intermediate-value-secQ', component_property='children')]
)
def asset(dat):
    statsQ = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsQ.loc[:, "cce"], x=statsQ.loc[:, "dates"], name='Ti???n v?? T??T',
                        marker=dict(color=('teal')))
    asset_bar2 = go.Bar(y=statsQ.loc[:, "bs_margin"], x=statsQ.loc[:, "dates"], name="Cho vay margin",
                        marker=dict(color=('green')))
    asset_bar3 = go.Bar(y=statsQ.loc[:, "bs_st_fvtpl"], x=statsQ.loc[:, "dates"], name="Ch???ng kho??n FVTPL",
                        marker=dict(color=('#A4DE02')))
    asset_bar4 = go.Bar(y=statsQ.loc[:, "bs_afs"], x=statsQ.loc[:, "dates"], name="Ch???ng kho??n AFS",
                        marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar5 = go.Bar(y=statsQ.loc[:, "bs_htm"], x=statsQ.loc[:, "dates"], name="Ch???ng kho??n HTM",
                        marker=dict(color=('orange')))
    asset_bar6 = go.Bar(y=statsQ.loc[:, "bs_jv"], x=statsQ.loc[:, "dates"], name="LDLK",
                        marker=dict(color=('deeppink')))
    asset_bar7 = go.Bar(y=statsQ.loc[:, "other_asset"], x=statsQ.loc[:, "dates"], name="Kh??c",
                        marker=dict(color=('darkgray')))
    asset_bar9 = go.Scatter(y=statsQ.loc[:, "margin/E"], x=statsQ.loc[:, "dates"], yaxis='y2',
                            name="Margin/E", line=dict(color='deeppink', width=4,dash='dot'),
                            mode='lines')
    asset_bar8 = go.Scatter(y=statsQ.loc[:, "mc"], x=statsQ.loc[:, "dates"], yaxis='y',
                            name="V???n h??a", line=dict(color='darkturquoise', width=4),
                            mode='lines+markers')
    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4,
                  asset_bar5, asset_bar6, asset_bar7,asset_bar8,asset_bar9]
                  # asset_bar8,asset_bar9]

    fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'
                                , xaxis=dict(tickformat='%Y-%b')
                                , yaxis=go.layout.YAxis(gridwidth=3  # ,hoverformat = '.1f'
                                                        )
                                , yaxis2=go.layout.YAxis(showgrid=False, tickformat='.2%',
                                                         overlaying='y', side='right')
                                , title='C?? c???u t??i s???n'
                                , legend=dict(x=1.1, y=1)
                                ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')



@app.callback(
    Output(component_id='output-graph-secQ-4', component_property='figure'),
    [Input(component_id='intermediate-value-secQ', component_property='children')]
)
def equity(dat):
    statsQ = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsQ.loc[:, "cap_e"], x=statsQ.loc[:, "dates"], name="V???n ??i???u l???",
                        marker=dict(color=('green')))
    asset_bar2 = go.Bar(y=statsQ.loc[:, "re"], x=statsQ.loc[:, "dates"], name="LN ch??a ph??n ph???i",
                        marker=dict(color=('#A4DE02')))
    asset_bar3 = go.Bar(y=statsQ.loc[:, "quy_duphong"], x=statsQ.loc[:, "dates"], name="Qu??? d??? ph??ng")
    asset_bar4 = go.Bar(y=statsQ.loc[:, "other_equity"], x=statsQ.loc[:, "dates"],
                        name="V???n kh??c", marker=dict(color=('pink')))
    asset_bar5 = go.Bar(y=statsQ.loc[:, "st_debt"], x=statsQ.loc[:, "dates"], name="Vay ng???n h???n",
                        marker=dict(color=('orange')))
    asset_bar6 = go.Bar(y=statsQ.loc[:, "lt_debt"], x=statsQ.loc[:, "dates"], name='Vay d??i h???n',
                        marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar7 = go.Bar(y=statsQ.loc[:, "lia_bond"], x=statsQ.loc[:, "dates"], name="Tr??i phi???u",
                        marker=dict(color=('yellow')))
    asset_bar8 = go.Bar(y=statsQ.loc[:, "other_lia"], x=statsQ.loc[:, "dates"], name="N??? kh??c",
                        marker=dict(color=('darkgray')))
    asset_bar10 = go.Scatter(y=statsQ.loc[:, "E/A"], x=statsQ.loc[:, "dates"], yaxis='y2', name="E/A",
                             line=dict(color='deeppink', width=3, dash='dot'), mode='lines')
    asset_bar9 = go.Scatter(y=statsQ.loc[:, "mc"], x=statsQ.loc[:, "dates"], yaxis='y',
                            name="V???n h??a", line=dict(color='darkturquoise', width=4),
                            mode='lines+markers')

    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4, asset_bar5, asset_bar6, asset_bar7,
                  asset_bar8,asset_bar9,asset_bar10]
    fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'
                                , xaxis=dict(tickformat='%Y-%b')
                                , yaxis2=go.layout.YAxis(showgrid=False, tickformat='.1%', title='D/A', overlaying='y',
                                                         side='right')
                                , yaxis=go.layout.YAxis(gridwidth=4  # ,hoverformat = '.1f'
                                                        )
                                , title='C?? c???u ngu???n v???n'
                                , legend=dict(x=1.1, y=1)
                                ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')



@app.callback(
    Output(component_id='output-graph-secQ-5', component_property='figure'),
    [Input(component_id='intermediate-value-secQ', component_property='children')]
)
def growth(dat):
    statsQ = pd.read_json(dat, orient='split')
    asset_bar1 = go.Scatter(y=statsQ.loc[:, "roe_4Q"], x=statsQ.loc[:, "dates"],name="ROE_4Q",
                            line=dict(color='darkturquoise', width=4), mode='lines+markers')
    asset_bar2 = go.Scatter(y=statsQ.loc[:, "roa_4Q"], x=statsQ.loc[:, "dates"],name="ROA_4Q",
                            line=dict(color='orange', width=4), mode='lines+markers')
    asset_data = [asset_bar1, asset_bar2]
    fig = go.Figure(data=asset_data, layout=go.Layout(barmode='relative'
                                , xaxis=dict(showgrid=False,tickformat='%Y-%b')
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
    Output(component_id='output-graph-secQ-6', component_property='figure'),
    [Input(component_id='intermediate-value-secQ', component_property='children')]
)
def cf(dat):
    statsQ = pd.read_json(dat, orient='split')
    bar2 = go.Bar(y=statsQ.loc[:, "cfo"], x=statsQ.loc[:, "dates"], name="D??ng ti???n t??? kinh doanh",
                  marker=dict(color=('teal')))
    bar3 = go.Bar(y=statsQ.loc[:, "cfi"], x=statsQ.loc[:, "dates"], name="D??ng ti???n t??? ?????u t??",
                  marker=dict(color=('orange')))
    bar1 = go.Bar(y=statsQ.loc[:, "cf_div"], x=statsQ.loc[:, "dates"], name="C??? t???c ti???n m???t",
                  marker=dict(color=('rgb(200, 0, 0)')))
    bar4 = go.Bar(y=statsQ.loc[:, "cf_e_raise"], x=statsQ.loc[:, "dates"], name="T??ng v???n",
                  marker=dict(color=('deeppink')))
    bar5 = go.Bar(y=statsQ.loc[:, "cf_treasury"], x=statsQ.loc[:, "dates"], name="CP qu???",
                  marker=dict(color=('yellow')))
    bar6 = go.Bar(y=statsQ.loc[:, "other_cf"], x=statsQ.loc[:, "dates"], name="CF kh??c",
                  marker=dict(color=('darkgray')))
    tong = go.Scatter(y=statsQ.loc[:, "cf_tong"], x=statsQ.loc[:, "dates"],
                      name="T???ng d??ng ti???n (ph???i)", yaxis='y2', line=dict(color='darkturquoise', width=3),
                      mode='lines+markers')
    data_CF = [bar1, bar2, bar3, bar4, bar5, bar6, tong]
    fig = go.Figure(data=data_CF,
                    layout=go.Layout(barmode='relative',
                                     xaxis=dict(tickformat='%Y-%b')
                                     , yaxis=go.layout.YAxis(gridwidth=3, rangemode='tozero')
                                     , yaxis2=go.layout.YAxis(overlaying='y', side='right', showgrid=False,
                                                              rangemode='tozero')
                                     , title='D??ng ti???n'
                                     , legend=dict(x=1.1, y=1)
                                     ))
    return fig.update_layout(template='plotly_dark', title_x=0.5,
                             plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)')

@app.callback(
    Output(component_id='output-graph-secQ-7', component_property='figure'),
    [Input(component_id='intermediate-value-secQ', component_property='children')]
)
def pe(dat):
    statsQ = pd.read_json(dat, orient='split')
    bar1 = go.Scatter(y=statsQ.loc[:, "net_income_4Q"], x=statsQ.loc[:, "dates"], name='LNST 4Q',
                      line=dict(color='red', width=3,dash='dot'), mode='lines')
    bar2 = go.Scatter(y=statsQ.loc[:, "mc"], x=statsQ.loc[:, "dates"], name="V???n h??a (ph???i)",
                      line=dict(color='darkturquoise', width=3), mode='lines+markers', yaxis='y')
    bar3 = go.Scatter(y=statsQ.loc[:, "P/E"], x=statsQ.loc[:, "dates"], name="P/E (ph???i)",
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
    Output(component_id='output-graph-secQ-8', component_property='figure'),
    [Input(component_id='intermediate-value-secQ', component_property='children')]
)
def pb(dat):
    statsQ = pd.read_json(dat, orient='split')
    bar1 = go.Scatter(y=statsQ.loc[:, "te"], x=statsQ.loc[:, "dates"], name='Gi?? tr??? s??? s??ch',
                      line=dict(color='lavender', width=3), mode='lines+markers')
    bar2 = go.Scatter(y=statsQ.loc[:, "mc"], x=statsQ.loc[:, "dates"], name='V???n h??a',
                      line=dict(color='darkturquoise', width=3), mode='lines+markers')
    bar3 = go.Scatter(y=statsQ.loc[:, "roe_4Q"], x=statsQ.loc[:, "dates"], name="ROE (ph???i)",
                      line=dict(color='red', width=3,dash='dot'), mode='lines', yaxis='y2')

    # bar4 = go.Scatter(y=statsQ.loc[:, "P/B"], x=statsQ.loc[:, "dates"], name="P/B (ph???i)",
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
