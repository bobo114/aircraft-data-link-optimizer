import dash
from dash import dcc, html
from dash.dependencies import Output, Input, State
import plotly.graph_objects as go
from calculate_path import extrapolate_position, compute_los_path
from update_planes import get_planes

# -------------------------------
# Globals for selection
# -------------------------------
selection_mode = None  # "start" or "end"
selected_start_plane = None
selected_end_plane = None

planes_list = get_planes()

# -------------------------------
# Initialize Dash app
# -------------------------------
app = dash.Dash(__name__)

# -------------------------------
# Initial figure
# -------------------------------
fig = go.Figure()

# Trace 0 → aircraft (forecasted)
fig.add_trace(go.Scattermap(
    lat=[],
    lon=[],
    mode='markers+text',
    marker=dict(size=9, color='blue'),
    text=[],
    textposition="top right",
    name="Aircraft"
))

# Trace 1 → start/end markers
fig.add_trace(go.Scattermap(
    lat=[],
    lon=[],
    mode="markers",
    marker=dict(size=[], color=[]),
    name="Selections"
))

# Trace 2 → shortest LOS path
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
        html.Button("Update Positions", id="update-btn", n_clicks=0),
        html.Label("Forecast (seconds)"),
        dcc.Slider(
            id='forecast-slider',
            min=0,
            max=3600,
            step=60,
            value=0,
            marks={0: "0s", 600: "10m", 1200: "20m", 1800: "30m", 3600: "1h"},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ], style={"padding": "10px"}),

    dcc.Graph(id='map', figure=fig)
])

# -------------------------------
# Callback
# -------------------------------
@app.callback(
    Output('map', 'figure'),
    Input('start-btn', 'n_clicks'),
    Input('end-btn', 'n_clicks'),
    Input('calc-btn', 'n_clicks'),
    Input('update-btn', 'n_clicks'),
    Input('map', 'clickData'),
    Input('forecast-slider', 'value'),
    State('map', 'figure')
)
def update_map(start_clicks, end_clicks, calc_clicks, update_clicks, clickData, forecast_seconds, fig):
    global selection_mode, selected_start_plane, selected_end_plane, planes_list

    ctx = dash.callback_context
    triggered = ctx.triggered[0]['prop_id'].split('.')[0]

    # -----------------------
    # Button handling
    # -----------------------
    if triggered == "start-btn":
        selection_mode = "start"
        print("Click on a plane to select START")

    elif triggered == "end-btn":
        selection_mode = "end"
        print("Click on a plane to select END")

    elif triggered == "map" and clickData is not None:
        point_idx = clickData["points"][0]["pointIndex"]
        if selection_mode == "start":
            selected_start_plane = point_idx
            print(f"Start selected: {planes_list[point_idx]['icao24']}")
        elif selection_mode == "end":
            selected_end_plane = point_idx
            print(f"End selected: {planes_list[point_idx]['icao24']}")

    elif triggered == "update-btn":
        # Save ICAOs
        start_icao = planes_list[selected_start_plane]["icao24"] if selected_start_plane is not None else None
        end_icao = planes_list[selected_end_plane]["icao24"] if selected_end_plane is not None else None

        # Reload planes
        planes_list = get_planes()

        # Restore selections
        selected_start_plane = next(
            (i for i, p in enumerate(planes_list) if p["icao24"] == start_icao),
            None
        ) if start_icao else None

        selected_end_plane = next(
            (i for i, p in enumerate(planes_list) if p["icao24"] == end_icao),
            None
        ) if end_icao else None

    # -----------------------
    # Build forecasted planes list
    # -----------------------
    forecasted_planes = []
    for p in planes_list:
        lat, lon = extrapolate_position(
            p["lat"], p["lon"], p["velocity"], p["track"], forecast_seconds
        )
        newp = p.copy()
        newp["lat"] = lat
        newp["lon"] = lon
        forecasted_planes.append(newp)

    # -----------------------
    # Update aircraft trace
    # -----------------------
    fig['data'][0]['lat'] = [p["lat"] for p in forecasted_planes]
    fig['data'][0]['lon'] = [p["lon"] for p in forecasted_planes]
    fig['data'][0]['text'] = [p["callsign"] or p["icao24"] for p in forecasted_planes]

    # -----------------------
    # Update start/end markers
    # -----------------------
    markers_lat = []
    markers_lon = []
    colors = []
    sizes = []

    if selected_start_plane is not None and selected_start_plane < len(forecasted_planes):
        p = forecasted_planes[selected_start_plane]
        markers_lat.append(p["lat"])
        markers_lon.append(p["lon"])
        colors.append("green")
        sizes.append(14)

    if selected_end_plane is not None and selected_end_plane < len(forecasted_planes):
        p = forecasted_planes[selected_end_plane]
        markers_lat.append(p["lat"])
        markers_lon.append(p["lon"])
        colors.append("red")
        sizes.append(14)

    fig['data'][1]['lat'] = markers_lat
    fig['data'][1]['lon'] = markers_lon
    fig['data'][1]['marker']['size'] = sizes
    fig['data'][1]['marker']['color'] = colors

    # -----------------------
    # Update LOS path (USING FORECASTED POSITIONS)
    # -----------------------
    if triggered == "calc-btn" and selected_start_plane is not None and selected_end_plane is not None:
        shortest_los_path = compute_los_path(
            forecasted_planes,  # <<< critical fix
            forecasted_planes[selected_start_plane]["icao24"],
            forecasted_planes[selected_end_plane]["icao24"],
            extra_delay=0.0
        )

        if shortest_los_path:
            fig['data'][2]['lat'] = [p["lat"] for p in shortest_los_path]
            fig['data'][2]['lon'] = [p["lon"] for p in shortest_los_path]
        else:
            print("Cannot calculate LOS path")

    return fig

# -------------------------------
# Run app
# -------------------------------
def run():
    app.run(debug=True)


if __name__ == "__main__":
    run()
