import requests
import json
import pickle
import os
from datetime import datetime
import random

# Load your API client credentials
with open("../credentials.json") as f:
    creds = json.load(f)

# Token endpoint
TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"

data = {
    "grant_type": "client_credentials",
    "client_id": creds["clientId"],
    "client_secret": creds["clientSecret"]
}

def get_planes():
    # Get OAuth token
    r = requests.post(TOKEN_URL, data=data)
    r.raise_for_status()
    access_token = r.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Get states over Canada bounding box
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
        if plane[8]:  # skip if on-ground
            continue
        planes_list.append({
            "icao24": plane[0],
            "callsign": plane[1],
            "lat": plane[6],
            "lon": plane[5],
            "geo_alt": plane[13] if plane[13] else 0,
            "velocity": plane[9] if plane[9] and plane[10] else 0,
            "track": plane[10] if plane[10] else 0
        })

    # Create archives folder if it doesn't exist
    os.makedirs("archives", exist_ok=True)

    # Save to pickle with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"archives/planes_{timestamp}.pkl"
    with open(filename, "wb") as f:
        pickle.dump(planes_list, f)

    print(f"Saved {len(planes_list)} planes to {filename}")
    return planes_list
