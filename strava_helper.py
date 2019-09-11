from stravalib import Client
import pandas as pd
from functools import lru_cache


@lru_cache(maxsize=32)
def get_strava_some_activities_data(client):
    activities = client.get_activities(limit=100)
    data_of_interest = [
        'average_speed',
        'average_heartrate',
        'average_watts', 
        'distance',
        'elapsed_time',
        'total_elevation_gain',
        'type', 
        'start_date_local'
    ]

    data = []
    for activity in activities:
        data.append([activity.to_dict().get(x) for x in data_of_interest])

    return pd.DataFrame(data, columns=data_of_interest)