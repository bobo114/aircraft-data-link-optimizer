from opensky_api import OpenSkyApi
import dash
from dash import dcc, html
from dash.dependencies import Output, Input, State
import plotly.graph_objects as go

# Initialize OpenSky API
api = OpenSkyApi()

# Canada bounding box
min_lat, max_lat = 42.0, 90.0
min_lon, max_lon = -141.0, -52.0

# Create Dash app
app = dash.Dash(__name__)

# Base figure
base_fig = go.Figure(go.Scattergeo(
    lat=[],
    lon=[],
    mode='markers+text',
    marker=dict(size=5, color='red'),
    text=[],
    textposition='top center'
))

base_fig.update_geos(
    projection_type="orthographic",
    showcountries=True,
    showland=True,
    landcolor="lightgreen",
    oceancolor="lightblue",
    showocean=True,
)

base_fig.update_layout(
    title='Aircraft Positions over Canada (Live Globe)',
    geo=dict(
        showframe=False,
        showcoastlines=True,
    )
)

# Dash layout
app.layout = html.Div([
    html.H1("Live Aircraft Positions over Canada"),
    dcc.Graph(id='globe-graph', figure=base_fig),
    dcc.Interval(id='interval-component', interval=10*1000, n_intervals=0)
])

# Callback: update aircraft positions, preserve user view
@app.callback(
    Output('globe-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
    State('globe-graph', 'relayoutData')
)
def update_globe(n, relayout_data):
    states = api.get_states(bbox=(min_lat, max_lat, min_lon, max_lon))
    lats, lons, texts = [], [], []

    if states and states.states:
        for s in states.states:
            if s.latitude and s.longitude:
                lats.append(s.latitude)
                lons.append(s.longitude)
                texts.append(s.callsign.strip() if s.callsign else "N/A")

    # Update only the data
    base_fig.data[0].lat = lats
    base_fig.data[0].lon = lons
    base_fig.data[0].text = texts

    # Preserve user's current view if they moved/zoomed the globe
    if relayout_data:
        if 'geo.projection.rotation.lon' in relayout_data:
            base_fig.update_geos(projection_rotation=dict(
                lon=relayout_data.get('geo.projection.rotation.lon', 0),
                lat=relayout_data.get('geo.projection.rotation.lat', 0),
                roll=relayout_data.get('geo.projection.rotation.roll', 0)
            ))
        if 'geo.lonaxis.range' in relayout_data and 'geo.lataxis.range' in relayout_data:
            base_fig.update_geos(
                lonaxis_range=relayout_data['geo.lonaxis.range'],
                lataxis_range=relayout_data['geo.lataxis.range']
            )

    return base_fig

if __name__ == '__main__':
    app.run(debug=True)
