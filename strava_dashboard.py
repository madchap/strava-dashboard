#!/usr/bin/env python3

import time
import json

from flask import Flask, render_template, request, redirect
import plotly
import plotly.graph_objs as go
from stravalib import Client, exc
import pandas as pd

import strava_helper
import _creds


app = Flask(__name__)
# strava client
client = Client()

def create_plot(feature):
    df = strava_helper.get_strava_some_activities_data(client)
    print(f"dataframe", df)
    data = []


    if feature == 'Bar':
        df = pd.DataFrame(
            {'x': df['start_date_local'], 'y': df['total_elevation_gain']})
        data = [
            go.Bar(
                x=df['x'],  # assign x as the dataframe column 'x'
                y=df['y']
            )
        ]
    if feature == 'Line':
        df_elevation = pd.DataFrame(
            {'x': df['start_date_local'], 'y': df['total_elevation_gain']})
        df_heartrate = pd.DataFrame(
            {'x': df['start_date_local'], 'y': df['average_heartrate']})
        data = [
            go.Scatter(
                x=df_elevation['x'],
                y=df_elevation['y'],
                mode='lines+markers',
                showlegend=True,
                name='Elevation'
            ),
            go.Scatter(
                x=df_heartrate['x'],
                y=df_heartrate['y'],
                mode='lines+markers',
                showlegend=True,
                name='Avg heart rate',
                line_color='rgba(255,0,0,1)',
                connectgaps=True
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


def check_token_expiration():
    expire = client.token_expires_at
    if time.time() > expire:
        print("I have expired! Need a refresher.")
        refresh_response = client.refresh_access_token(client_id=_creds.client_id,
                                                       client_secret=_creds.client_secret,
                                                       refresh_token=client.refresh_token)
        client.access_token = refresh_response['access_token']
        client.refresh_token = refresh_response['refresh_token']
        client.token_expires_at = refresh_response['expires_at']


@app.route('/')
def index():
    if not authenticated():
        return start_auth('/')
    check_token_expiration()

    feature = 'Line'
    line = create_plot(feature)

    return render_template('index.html', plot=line)


@app.route('/bar', methods=['GET', 'POST'])
def change_features():
    if not authenticated():
        return start_auth('/bar')
    check_token_expiration()

    feature = request.args['selected']
    graphJSON = create_plot(feature)

    return graphJSON


@app.route('/start_auth', methods=['GET'])
def start_auth(b=None):
    url = client.authorization_url(
        client_id=_creds.client_id, redirect_uri='http://localhost:5000/finish_auth?return_to=' + b)
    return redirect(url, code=302)


@app.route('/finish_auth', methods=['GET'])
def finish_auth():
    code = request.args.get('code')
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


@app.route('/logout', methods=['GET'])
def logout():
    try:
        client.deauthorize()
        return "You're now deauthorized."
    except exc.AccessUnauthorized:
        return "You were likely already logged out from Strava."


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
