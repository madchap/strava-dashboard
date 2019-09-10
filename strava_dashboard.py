from flask import Flask, render_template, request
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

def open_browser(te, url):
    print("before waiting browser")
    webbrowser.open(url)
    print("after opening browser")
    #try:
    #    code = request.args.get('code')
    #    print(f"My code is {code}")
    #    te.set()
    #except Exception as e:
    #    print(str(e))

@app.route('/')
def index():
    try:
        print(f"Do I have a token?", client.access_token)
        feature = 'Bar'
        bar = create_plot(feature)
    except exc.Fault:
        print("Need to authenticate.")
        auth_dance()
    
    return render_template('index.html', plot=bar)


@app.route('/bar', methods=['GET', 'POST'])
def change_features():
    feature = request.args['selected']
    graphJSON = create_plot(feature)

    return graphJSON

@app.route('/auth', methods=['GET'])
def auth_dance():
    # te = threading.Event()
    try:
        expire = client.token_expires_at
        print(f"I expire at {expire}")
        if time.time() > expire:
            print("I have expired! Need a refresher.")
            refresh_response = client.refresh_access_token(client_id=_creds.client_id,
                                                        client_secret=_creds.client_secret)
            
            client.access_token = refresh_response['access_token']
            client.refresh_token = refresh_response['refresh_token']
            client.token_expires_at = refresh_response['expires_at']
    except:
        url = client.authorization_url(client_id=_creds.client_id, redirect_uri='http://localhost:5000/auth')
        print("Starting authorization process.")

        # while not (te.isSet()):
       #      browser_thread = threading.Thread(name='browser', target=open_browser, args=(te, url))
      #       browser_thread.start()
# 
#             print("Waiting for authz..")
#             done = te.wait()
#             if done:
#                 print("Done waiting. Moving on. Could get token code here?")
#             else:
#                 print("Whatever.")
#
        webbrowser.open(url)
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

    return 'Return to your original tab, you\'re now authorized.'

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
