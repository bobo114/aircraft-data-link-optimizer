import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import plotly.graph_objects as go
import pickle
from calculate_path import extrapolate_position, compute_los_path
import time

# -------------------------------
# Globals for time + selection
# -------------------------------
last_update_time = time.time()
selection_mode = None  # "start" or "end"
selected_start_plane = None
selected_end_plane = None

# -------------------------------
# Load planes from pickle
# -------------------------------
with open("../tests/planes_canada.pkl", "rb") as f:
    planes_data = pickle.load(f)

planes_list = []
for plane in planes_data.get("states", []):
    if plane[8]:  # skip planes on ground
        continue
    planes_list.append({
        "icao24": plane[0],
        "callsign": plane[1].strip() if plane[1] else None,
        "lat": plane[6],
        "lon": plane[5],
        "geo_alt": plane[13] if plane[13] else 0,
        "velocity": plane[9] if plane[9] else 0,
        "track": plane[10] if plane[10] else 0
    })

# -------------------------------
# Initialize Dash app
# -------------------------------
app = dash.Dash(__name__)

# -------------------------------
# Initial figure
# -------------------------------
fig = go.Figure()

# Trace 0 → planes
fig.add_trace(go.Scattermap(
    lat=[p["lat"] for p in planes_list],
    lon=[p["lon"] for p in planes_list],
    mode='markers+text',
    marker=dict(size=9, color='blue'),
    text=[p["callsign"] or p["icao24"] for p in planes_list],
    textposition="top right",
    name="Aircraft"
))

# Trace 1 → start/end points (empty initially)
fig.add_trace(go.Scattermap(
    lat=[],
    lon=[],
    mode="markers",
    marker=dict(size=[], color=[]),
    name="Selections"
))

# Trace 2 → shortest LOS path (empty initially)
fig.add_trace(go.Scattermap(
    lat=[],
    lon=[],
    mode="lines+markers",
    line=dict(color="orange", width=3),
    marker=dict(size=8, color="orange"),
    name="LOS Path"
))



fig.update_layout(
    mapbox=dict(
        style="open-street-map",
        center=dict(lat=45.0, lon=-76.0),
        zoom=4
    ),
    margin=dict(l=0, r=0, t=0, b=0),
    uirevision="constant"
)

# -------------------------------
# Layout
# -------------------------------
app.layout = html.Div([
    html.Div([
        html.Button("Select Start", id="start-btn", n_clicks=0),
        html.Button("Select End", id="end-btn", n_clicks=0),
        html.Button("Calculate", id="calc-btn", n_clicks=0),
    ], style={"padding": "10px"}),

    dcc.Graph(id='map', figure=fig),
    dcc.Interval(id='interval', interval=200, n_intervals=0)
])

# -------------------------------
# Callback
# -------------------------------
@app.callback(
    Output('map', 'figure'),
    Input('interval', 'n_intervals'),
    Input('start-btn', 'n_clicks'),
    Input('end-btn', 'n_clicks'),
    Input('calc-btn', 'n_clicks'),
    Input('map', 'clickData'),
)
def update_map(n, start_clicks, end_clicks, calc_clicks, clickData):
    global last_update_time, selection_mode, selected_start_plane, selected_end_plane

    ctx = dash.callback_context
    triggered = ctx.triggered[0]['prop_id'].split('.')[0]

    # -----------------------
    # Button handling
    # -----------------------
    if triggered == "start-btn":
        selection_mode = "start"
        print("Click on a plane to select START point")

    elif triggered == "end-btn":
        selection_mode = "end"
        print("Click on a plane to select END point")

    elif triggered == "calc-btn":
        print("CALCULATE pressed")
        start_plane = planes_list[selected_start_plane]["icao24"] if selected_start_plane is not None else None
        end_plane = planes_list[selected_end_plane]["icao24"] if selected_end_plane is not None else None
        print("Start plane:", start_plane)
        print("End plane:", end_plane)
        if start_plane and end_plane:
            shortest_los_path = compute_los_path(planes_list, start_plane, end_plane, extra_delay=0.0)
            print("Shortest LOS path:", [i["callsign"] for i in shortest_los_path])
            if shortest_los_path:
                print("Drawing shortest LOS path on map...")
                lats = [plane["lat"] for plane in shortest_los_path]
                lons = [plane["lon"] for plane in shortest_los_path]
                fig.data[2].lat = lats
                fig.data[2].lon = lons
        return fig

    # -----------------------
    # Map click handling (plane selection)
    # -----------------------
    elif triggered == "map" and clickData is not None:
        point_idx = clickData["points"][0]["pointIndex"]  # index in planes trace
        if selection_mode == "start":
            selected_start_plane = point_idx
            print(f"Start selected: plane {planes_list[point_idx]['icao24']}")
        elif selection_mode == "end":
            selected_end_plane = point_idx
            print(f"End selected: plane {planes_list[point_idx]['icao24']}")

    # -----------------------
    # Update aircraft positions
    # -----------------------
    time_now = time.time()
    dt = time_now - last_update_time
    for plane in planes_list:
        plane["lat"], plane["lon"] = extrapolate_position(
            plane["lat"],
            plane["lon"],
            plane["velocity"],
            plane["track"],
            dt
        )
    last_update_time = time_now

    # Update aircraft trace
    fig.data[0].lat = [p["lat"] for p in planes_list]
    fig.data[0].lon = [p["lon"] for p in planes_list]
    fig.data[0].text = [p["callsign"] or p["icao24"] for p in planes_list]

    # -----------------------
    # Update start/end markers (following planes)
    # -----------------------
    markers_lat = []
    markers_lon = []
    colors = []
    sizes = []

    if selected_start_plane is not None:
        plane = planes_list[selected_start_plane]
        markers_lat.append(plane["lat"])
        markers_lon.append(plane["lon"])
        colors.append("green")
        sizes.append(14)

    if selected_end_plane is not None:
        plane = planes_list[selected_end_plane]
        markers_lat.append(plane["lat"])
        markers_lon.append(plane["lon"])
        colors.append("red")
        sizes.append(14)

    fig.data[1].lat = markers_lat
    fig.data[1].lon = markers_lon
    fig.data[1].marker.size = sizes
    fig.data[1].marker.color = colors

    return fig

# -------------------------------
# Run app
# -------------------------------
if __name__ == '__main__':
    app.run(debug=True)
