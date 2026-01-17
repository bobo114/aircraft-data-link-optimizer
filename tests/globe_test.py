from opensky_api import OpenSkyApi
import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import plotly.graph_objects as go

api = OpenSkyApi()

min_lat, max_lat = 42.0, 90.0
min_lon, max_lon = -141.0, -52.0

app = dash.Dash(__name__)

# Initial empty globe
fig = go.Figure(go.Scattergeo(
    lat=[],
    lon=[],
    mode='markers',
    marker=dict(size=6, color='red')
))

fig.update_geos(
    projection_type="orthographic",
    showcountries=True,
    showland=True,
    showocean=True,
    landcolor="rgb(230,230,230)",
    oceancolor="rgb(200,220,255)"
)

fig.update_layout(
    title="Live Aircraft Globe",
    uirevision="keep"   # THIS is the magic line
)

app.layout = html.Div([
    dcc.Graph(id="globe", figure=fig),
    dcc.Interval(id="timer", interval=5000, n_intervals=0)
])

@app.callback(
    Output("globe", "extendData"),
    Input("timer", "n_intervals")
)
def update(n):
    states = api.get_states(bbox=(min_lat, max_lat, min_lon, max_lon))

    lats, lons = [], []
    if states and states.states:
        for s in states.states:
            if s.latitude and s.longitude:
                lats.append(s.latitude)
                lons.append(s.longitude)

    # This only moves the points, nothing else
    return (
        dict(lat=[lats], lon=[lons]),
        [0],      # update trace index 0
        0         # replace old data, don’t append
    )

if __name__ == "__main__":
    app.run(debug=True)
