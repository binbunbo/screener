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

from app import server

col = pd.read_excel('D:/Data/6.Python/project2/VND-col-bank.xlsx')
list_bank = pd.read_pickle('D:/Data/list_bank')
col1 = ['gp', 'op', 'op1', 'EBT', 'pretax_inc', 'net_income', 'ni_parent', 'core_e']
col3 = ['rev', 'gp', 'op', 'EBT', 'pretax_inc', 'net_income', 'ni_parent', 'core_e']

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

# def margin_func(x, i):
#     x[i + "m"] = x[i] / x['rev']
#
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
# def add_stats(x):
#     x['roe'] = x['net_income'] / x.sort_index(level=[0, 1])['te'].groupby(level=[0]).apply(
#         lambda x: x.rolling(2, min_periods=2).mean())
#     x['roic'] = x['net_income'] / x.sort_index(level=[0, 1])['ic'].groupby(level=[0]).apply(
#         lambda x: x.rolling(2, min_periods=2).mean())
#     x['roa'] = x['net_income'] / x.sort_index(level=[0, 1])['ta'].groupby(level=[0]).apply(
#         lambda x: x.rolling(2, min_periods=2).mean())
#     x['EBToe_core'] = x['EBT'] / x.sort_index(level=[0, 1])['te'].groupby(level=[0]).apply(
#         lambda x: x.rolling(2, min_periods=2).mean())
#     x['roe_core'] = x['EBToe_core'] * (1 - x['tax_rate'])
#     x['DE'] = x['debt'] / x['te']
#     x['DA'] = x['debt'] / x['ta']
#     x['ca/ta'] = x['ca'] / x['ta']
#     x['asset_turn'] = x['rev'] / x.sort_index(level=[0, 1])['ta'].groupby(level=[0]).apply(
#         lambda x: x.rolling(2, min_periods=2).mean())
#     x['ar_turn'] = x['rev'] / x.sort_index(level=[0, 1])['bs_ar'].groupby(level=[0]).apply(
#         lambda x: x.rolling(2, min_periods=2).mean())
#     x['ap_turn'] = (x['rev'] - x['gp']) / x.sort_index(level=[0, 1])['bs_ap'].groupby(level=[0]).apply(
#         lambda x: x.rolling(2, min_periods=2).mean())
#     x['inven_turn'] = (x['rev'] - x['gp']) / x.sort_index(level=[0, 1])['net_inven'].groupby(level=[0]).apply(
#         lambda x: x.rolling(2, min_periods=2).mean())


def add_dfQ(ticker):
    ticker = ticker.upper()
    x = get_bankQ(ticker)
    add_ratios(x)
    # for i in col1:
    #     margin_func(x,i)
    # for i in col3:
    #     g_func(x, i)
    # add_stats(x)
    return x


layout = html.Div(children=[
    html.Header(children='Graph bank Quý', className='ml-4',
                style={'font-size': '30px', 'font-weight': 'bold', 'font-family': 'Arial', 'text-align': 'center'}),
    html.Div(children='''Chọn mã CK và nhấn Enter:''', className='ml-4', style={'font-size': '20px'}),
    dcc.Input(id='input', value='VCB', type='text', debounce=True, className='ml-4'),
    html.Div(id='intermediate-value4', style={'display': 'none'}),
    html.Div([
        html.Div([dcc.Graph(id='output-graph41')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph42')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph43')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph44')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph45')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph46')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='output-graph47')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='output-graph48')], className='six columns',
                 style={'width': '50%', 'display': 'inline-block'}),
    ], className='row')
])


@app.callback(Output('intermediate-value4', 'children'), [Input(component_id='input', component_property='value')])
def clean_data(ticker):
    statsQ = add_dfQ(ticker)
    statsQ = statsQ.reset_index()
    statsQ['dates'] = pd.PeriodIndex(year=statsQ.reset_index()["year"], quarter=statsQ.reset_index()["quarter"])
    statsQ['dates'] = statsQ['dates'].dt.to_timestamp(freq='Q')
    statsQ = statsQ.set_index('ticker')
    return statsQ.to_json(date_format='iso', orient='split')


@app.callback(
    Output(component_id='output-graph42', component_property='figure'),
    [Input(component_id='intermediate-value4', component_property='children')]
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
    Output(component_id='output-graph41', component_property='figure'),
    [Input(component_id='intermediate-value4', component_property='children')]
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
    Output(component_id='output-graph43', component_property='figure'),
    [Input(component_id='intermediate-value4', component_property='children')]
)
def asset(dat):
    statsQ = pd.read_json(dat, orient='split')
    asset_bar1 = go.Bar(y=statsQ.loc[:, "bs_cash"], x=statsQ.loc[:, "dates"], name='Tiền+ĐTNH',
                        marker=dict(color=('teal')))
    asset_bar2 = go.Bar(y=statsQ.loc[:, "asset_trading_ck"], x=statsQ.loc[:, "dates"], name="Chứng khoán KD",
                        marker=dict(color=('#A4DE02')))
    asset_bar3 = go.Bar(y=statsQ.loc[:, "asset_invest_ck"], x=statsQ.loc[:, "dates"], name="Chứng khoán đầu tư",
                        marker=dict(color=('green')))
    asset_bar4 = go.Bar(y=statsQ.loc[:, "net_asset_loan"], x=statsQ.loc[:, "dates"], name="Cho vay khách hàng",
                        marker=dict(color=('rgb(200, 0, 0)')))
    asset_bar5 = go.Bar(y=statsQ.loc[:, "asset_lt_inv"], x=statsQ.loc[:, "dates"], name="Đầu tư dài hạn",
                        marker=dict(color=('orange')))
    asset_bar6 = go.Bar(y=statsQ.loc[:, "bs_fa"], x=statsQ.loc[:, "dates"], name="TSCĐ",
                        marker=dict(color=('deeppink')))
    asset_bar7 = go.Bar(y=statsQ.loc[:, "other_asset"], x=statsQ.loc[:, "dates"], name="Khác",
                        marker=dict(color=('darkgray')))
    asset_bar8 = go.Scatter(y=statsQ.loc[:, "npl"], x=statsQ.loc[:, "dates"], yaxis='y2',
                            name="NPL", line=dict(color='darkturquoise', width=4),
                            mode='lines+markers')
    asset_bar9 = go.Scatter(y=statsQ.loc[:, "problem_asset_pct"], x=statsQ.loc[:, "dates"], yaxis='y2',
                            name="Problem asset (incl. VAMC)", line=dict(color='rgb(191, 214, 48)', width=4),
                            mode='lines+markers')
    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4,
                  asset_bar5, asset_bar6, asset_bar7,
                  asset_bar8,asset_bar9]

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
    Output(component_id='output-graph44', component_property='figure'),
    [Input(component_id='intermediate-value4', component_property='children')]
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

    asset_bar10 = go.Scatter(y=statsQ.loc[:, "casa"], x=statsQ.loc[:, "dates"], yaxis='y2',name="CASA",
                            line=dict(color='rgb(191, 214, 48)', width=4), mode='lines')
    asset_bar11 = go.Scatter(y=statsQ.loc[:, "E/A"], x=statsQ.loc[:, "dates"], yaxis='y2', name="E/A",
                             line=dict(color='darkturquoise', width=4,dash='dot'), mode='lines')
    asset_data = [asset_bar1, asset_bar2, asset_bar3, asset_bar4, asset_bar5, asset_bar6, asset_bar7,
                  asset_bar8,asset_bar9,asset_bar10,asset_bar11]
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



# @app.callback(
#     Output(component_id='output-graph47', component_property='figure'),
#     [Input(component_id='intermediate-value4', component_property='children')]
# )
# def growth(ticker):
#     ticker = ticker.upper()
#     g1 = go.Scatter(y=statsQ.loc[ticker, "g_rev"], x=statsQ.loc[ticker, "g_rev"].index, name="Sales Growth", yaxis="y2",
#                     line=dict(color='red', width=4), mode='lines+markers')
#     g2 = go.Scatter(y=statsQ.loc[ticker, "g_core_e"], x=statsQ.loc[ticker, "g_core_e"].index, name="Core E Growth",
#                     yaxis="y2", line=dict(color='green', width=4), mode='lines+markers')
#     g3 = go.Scatter(y=statsQ.loc[ticker, "g_net_income"], x=statsQ.loc[ticker, "g_net_income"].index, name="NI Growth",
#                     yaxis="y2", line=dict(color='yellow', width=4), mode='lines+markers')
#     g4 = go.Bar(y=statsQ.loc[ticker, "mc"], x=statsQ.loc[ticker, "mc"].index, name='Vốn hóa',
#                 marker=dict(color=('rgb(20, 50, 90)')))
#
#     return {'data': [g1, g2, g3, g4],
#             'layout': go.Layout(title='Tăng trưởng',
#                                 xaxis=dict(tickvals=statsQ.loc[ticker].index, showgrid=False),
#                                 yaxis2=go.layout.YAxis(tickformat='.1%', gridwidth=4, overlaying="y", side="right",
#                                                        showgrid=False, range=[-0.5, 1])
#                                 , legend=dict(x=1.1, y=1)
#                                 )
#
#             }


# @app.callback(
#     Output(component_id='output-graph48', component_property='figure'),
#     [Input(component_id='intermediate-value4', component_property='children')]
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
#                       name="Tổng dòng tiền (phải)", yaxis='y2', line=dict(color='black', width=4), mode='lines+markers')
#     data_CF = [bar1, bar2, bar3, bar4, bar5, bar6, bar7, bar10, tong]
#
#     return {'data': data_CF,
#             'layout': go.Layout(barmode='relative',
#                                 xaxis=dict(tickvals=statsQ.loc[ticker].index)
#                                 , yaxis=go.layout.YAxis(gridwidth=4, rangemode='tozero'  # hoverformat = '.1f'
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
#     Output(component_id='output-graph45', component_property='figure'),
#     [Input(component_id='intermediate-value4', component_property='children')]
# )
# def pe(ticker):
#     ticker = ticker.upper()
#     bar1 = go.Scatter(y=statsQ.loc[ticker, "net_income"], x=statsQ.loc[ticker, "net_income"].index, name='Lãi/Lỗ 4Q',
#                       line=dict(color='rgb(20, 50, 90)', width=4), mode='lines+markers')
#     bar2 = go.Scatter(y=statsQ.loc[ticker, "core_e"], x=statsQ.loc[ticker, "core_e"].index, name='Lãi/Lỗ core 4Q',
#                       line=dict(color='#A4DE02', width=4), mode='lines+markers')
#     bar3 = go.Scatter(y=statsQ.loc[ticker, "mc"], x=statsQ.loc[ticker, "mc"].index, name="Vốn hóa (phải)",
#                       line=dict(color='red', width=4), mode='lines+markers', yaxis='y2')
#
#     data_PE = [bar1, bar2, bar3]
#
#     return {'data': data_PE,
#             'layout': go.Layout(xaxis=dict(showgrid=False)
#                                 , yaxis=go.layout.YAxis(gridwidth=4)
#                                 , yaxis_type='log'
#                                 , yaxis2=go.layout.YAxis(overlaying='y', side='right', showgrid=False)
#                                 , title='P/E'
#                                 , legend=dict(x=1.1, y=1)
#                                 )
#
#             }


# @app.callback(
#     Output(component_id='output-graph46', component_property='figure'),
#     [Input(component_id='intermediate-value4', component_property='children')]
# )
# def pb(ticker):
#     ticker = ticker.upper()
#     bar1 = go.Scatter(y=statsQ.loc[ticker, "te"], x=statsQ.loc[ticker, "te"].index, name='Book value',
#                       line=dict(color='rgb(20, 50, 90)', width=4), mode='lines+markers')
#     bar2 = go.Scatter(y=statsQ.loc[ticker, "mc"], x=statsQ.loc[ticker, "mc"].index, name='Vốn hóa',
#                       line=dict(color='red', width=4), mode='lines+markers')
#     bar3 = go.Scatter(y=statsQ.loc[ticker, "roe"], x=statsQ.loc[ticker, "roe"].index, name="ROE (phải)",
#                       line=dict(color='#A4DE02', width=4), mode='lines+markers', yaxis='y2')
#     bar4 = go.Scatter(y=statsQ.loc[ticker, "roe_core"], x=statsQ.loc[ticker, "roe_core"].index, name="ROE_core (phải)",
#                       line=dict(color='orange', width=4), mode='lines+markers', yaxis='y2')
#
#     data_PB = [bar1, bar2, bar3, bar4]
#
#     return {'data': data_PB,
#             'layout': go.Layout(barmode='relative',
#                                 xaxis=dict(
#                                     showgrid=False)
#                                 , yaxis=go.layout.YAxis(gridwidth=4)
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
