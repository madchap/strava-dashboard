#!/usr/bin/env python3

from flask import Flask, render_template, request, url_for, redirect
import webbrowser
import plotly
import plotly.graph_objs as go
from stravalib import Client, exc
import time
import os
import threading

import pandas as pd
import numpy as np
import json

import strava_helper
import _creds


app = Flask(__name__)

# strava client
client = Client()

def create_plot(feature):
    df = strava_helper.get_strava_some_activities_data(client)
    print(f"dataframe", df)

    if feature == 'Bar':
        df = pd.DataFrame({'x': df['start_date_local'], 'y': df['total_elevation_gain']})
        data = [
            go.Bar(
                x=df['x'], # assign x as the dataframe column 'x'
                y=df['y']
            )
        ]

    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON

def authenticated():
    try:
        client.token_expires_at
    except AttributeError:
        return False
    return client.token_expires_at is not None

@app.route('/')
def index():
    if not authenticated(): return start_auth('/')
    check_token_expiration()

    feature = 'Bar'
    bar = create_plot(feature)
    
    return render_template('index.html', plot=bar)


@app.route('/bar', methods=['GET', 'POST'])
def change_features():
    if not authenticated(): return start_auth('/bar')
    check_token_expiration()

    feature = request.args['selected']
    graphJSON = create_plot(feature)

    return graphJSON

@app.route('/start_auth', methods=['GET'])
def start_auth(b=None):
    url = client.authorization_url(client_id=_creds.client_id, redirect_uri='http://localhost:5000/finish_auth?return_to=' + b)
    return redirect(url, code=302)

def check_token_expiration():
    expire = client.token_expires_at
    print(f"I expire at {expire}")
    if time.time() > expire:
        print("I have expired! Need a refresher.")
        refresh_response = client.refresh_access_token(client_id=_creds.client_id,
                                                    client_secret=_creds.client_secret)
        
        client.access_token = refresh_response['access_token']
        client.refresh_token = refresh_response['refresh_token']
        client.token_expires_at = refresh_response['expires_at']

@app.route('/finish_auth', methods=['GET'])
def finish_auth():
    code = request.args.get('code')
    print(f"My code is {code}")
    token_response = client.exchange_code_for_token(client_id=_creds.client_id,
                                                client_secret=_creds.client_secret,
                                                code=code)
    access_token = token_response['access_token']
    refresh_token = token_response['refresh_token']
    expires_at = token_response['expires_at']

    client.access_token = access_token
    client.refresh_token = refresh_token
    client.token_expires_at = expires_at

    return_to = request.args.get('return_to')
    return redirect('/no_return_to' if return_to is None else return_to, code=302)

    #return 'Return to your original tab, you\'re now authorized.'

@app.route('/logout', methods=['GET'])
def logout():
    print("Deauthorizing!")
    try:
        client.deauthorize()
        return "You're now deauthorized."
    except exc.AccessUnauthorized as e:
        return "You were likely already logged out from Strava."


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
