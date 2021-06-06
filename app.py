#!/usr/bin/env python
# coding: utf-8

import dash
import dash_bootstrap_components as dbc


app = dash.Dash(__name__, suppress_callback_exceptions=True,
                meta_tags=[{'name': 'viewport','content': 'width=device-width, initial-scale=1.0'}],
                external_stylesheets=[dbc.themes.DARKLY])
server = app.server

