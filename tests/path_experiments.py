import pickle
import random
from src.calculate_path import compute_los_path
import plotly.graph_objects as go

with open("planes_canada.pkl", "rb") as f:
    planes_data = pickle.load(f)

planes_list = []
for plane in planes_data.get("states", []):
    if plane[8]:
        continue
    planes_list.append({
        "icao24": plane[0],
        "callsign": plane[1].strip() if plane[1] else None,
        "lat": plane[6],
        "lon": plane[5],
        "geo_alt": plane[13] if plane[13] else 0
    })

# Example: pick two planes from the list
start_icao = planes_list[int(len(planes_list)*random.random())]['icao24']
end_icao   = planes_list[int(len(planes_list)*random.random())]['icao24']

# Call with custom extra_delay
path_nodes = compute_los_path(planes_list, start_icao, end_icao, extra_delay=0.01)
if path_nodes:
    print("Path:")
    for n in path_nodes:
        print(f"{n['callsign']} ({n['icao24']}), alt={n['geo_alt']}m, lat={n['lat']}, lon={n['lon']}")
    # ---------------------------
    # Plotting on globe
    # ---------------------------
    # Extract lat/lon for path
    path_lats = [p['lat'] for p in path_nodes]
    path_lons = [p['lon'] for p in path_nodes]
    path_callsigns = [f"{p['callsign']}, {p['geo_alt']}'" for p in path_nodes]

    # Plot all planes as faint points
    all_lats = [p['lat'] for p in planes_list]
    all_lons = [p['lon'] for p in planes_list]
    all_callsigns = [f"{p['callsign']}, {p['geo_alt']}'" for p in planes_list]

    fig = go.Figure()

    # All planes
    fig.add_trace(go.Scattergeo(
        lon=all_lons,
        lat=all_lats,
        mode='markers',
        marker=dict(size=3, color='lightgray'),
        text=all_callsigns,
        name='Planes'
    ))

    # Path line
    fig.add_trace(go.Scattergeo(
        lon=path_lons,
        lat=path_lats,
        mode='lines+markers+text',
        marker=dict(size=6, color='red'),
        line=dict(width=2, color='red'),
        text=path_callsigns,
        textposition='top center',
        name='Path'
    ))

    fig.update_layout(
        title_text="Shortest LOS Path Ottawa → Vancouver via Planes",
        geo=dict(
            projection_type='orthographic',
            showcountries=True,
            showland=True,
            landcolor='rgb(243,243,243)',
            countrycolor='rgb(204,204,204)',
            showocean=True,
            oceancolor='rgb(204, 224, 255)',
            lataxis_range=[30, 60],
            lonaxis_range=[-140, -50]
        )
    )

    fig.show()
else:
    print("No LOS path found")


