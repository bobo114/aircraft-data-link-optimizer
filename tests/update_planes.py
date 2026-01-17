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
print(f"Number of planes returned: {len(planes_data.get('states', []))}")

# 3. Save to disk using pickle
with open("planes_canada.pkl", "wb") as f:
    pickle.dump(planes_data, f)

print("Data saved to planes_canada.pkl")
