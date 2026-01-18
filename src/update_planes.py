import requests
import json
import pickle

# Load your API client credentials
with open("../credentials.json") as f:
    creds = json.load(f)

# 1. Get OAuth token
TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"

data = {
    "grant_type": "client_credentials",
    "client_id": creds["clientId"],
    "client_secret": creds["clientSecret"]
}
def get_planes():
    r = requests.post(TOKEN_URL, data=data)
    r.raise_for_status()
    access_token = r.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # 2. Get states over Canada bounding box
    url = "https://opensky-network.org/api/states/all"
    params = {
        "lamin": 40.0,
        "lamax": 85.0,
        "lomin": -150.0,
        "lomax": -50.0
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    planes_data = response.json()
    planes_list = []
    for plane in planes_data.get("states", []):
        if plane[8]:
            continue
        planes_list.append({
            "icao24": plane[0],
            "callsign": plane[1],
            "lat": plane[6],
            "lon": plane[5],
            "geo_alt": plane[13] if plane[13] else 0,
            "velocity": plane[9],
            "true_track": plane[10]
        })
    return planes_list