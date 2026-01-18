import pickle
import math
import heapq
import plotly.graph_objects as go

# ---------------------------
# Helpers (same as before)
# ---------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def los_distance(alt1, alt2):
    R = 6371000
    h1 = alt1 if alt1 and alt1 > 0 else 0
    h2 = alt2 if alt2 and alt2 > 0 else 0
    return math.sqrt(2*R*h1) + math.sqrt(2*R*h2)

# ---------------------------
# Load planes
# ---------------------------
with open("planes_canada.pkl", "rb") as f:
    planes_data = pickle.load(f)

planes_list = []
for plane in planes_data.get("states", []):
    if plane[8]:
        continue
    planes_list.append({
        "icao24": plane[0],
        "callsign": plane[1],
        "lat": plane[6],
        "lon": plane[5],
        "geo_alt": plane[13] if plane[13] else 0
    })

# ---------------------------
# Virtual nodes
# ---------------------------
start = {"icao24": "OTTAWA", "callsign": "OTTAWA", "lat": 45.4215, "lon": -75.6972, "geo_alt": 0}
end   = {"icao24": "VANCOUVER", "callsign": "VANCOUVER", "lat": 49.2827, "lon": -123.1207, "geo_alt": 0}
nodes = [start, end] + planes_list

# ---------------------------
# Graph construction
# ---------------------------
graph = {p['icao24']: [] for p in nodes}
for i, p1 in enumerate(nodes):
    for j, p2 in enumerate(nodes):
        if i >= j:
            continue
        d = haversine(p1['lat'], p1['lon'], p2['lat'], p2['lon'])
        max_los = los_distance(p1['geo_alt'], p2['geo_alt'])
        if d <= max_los:
            delay = d/300000 + 0.005
            graph[p1['icao24']].append((p2['icao24'], delay))
            graph[p2['icao24']].append((p1['icao24'], delay))

# ---------------------------
# Dijkstra
# ---------------------------
def dijkstra(graph, start, end):
    queue = [(0, start, [])]
    seen = set()
    while queue:
        total, node, path = heapq.heappop(queue)
        if node == end:
            return total, path + [node]
        if node in seen:
            continue
        seen.add(node)
        for neighbor, delay in graph.get(node, []):
            if neighbor not in seen:
                heapq.heappush(queue, (total + delay, neighbor, path + [node]))
    return None, None

total_delay, path = dijkstra(graph, "OTTAWA", "VANCOUVER")


# ---------------------------
# Map ICAO24 → callsign
# ---------------------------
icao_to_callsign = {p['icao24']: f"{p['callsign'].strip()}, {p['geo_alt']}'" if p['callsign'] else f"UNKNOWN-{p['icao24']}" for p in planes_list}
icao_to_callsign['OTTAWA'] = 'OTTAWA'
icao_to_callsign['VANCOUVER'] = 'VANCOUVER'

path_callsigns = [icao_to_callsign.get(icao, icao) for icao in path]
print("Path:", path_callsigns)
# ---------------------------
# Plotting on globe
# ---------------------------
# Extract lat/lon for path
path_lats = [next(p['lat'] for p in nodes if p['icao24']==icao) for icao in path]
path_lons = [next(p['lon'] for p in nodes if p['icao24']==icao) for icao in path]

# Plot all planes as faint points
all_lats = [p['lat'] for p in planes_list]
all_lons = [p['lon'] for p in planes_list]
all_callsigns = [f"{p['callsign']}, {p['geo_alt']}'" for p in planes_list]

fig = go.Figure()

# All planes
fig.add_trace(go.Scattergeo(
    lon = all_lons,
    lat = all_lats,
    mode='markers',
    marker=dict(size=3, color='lightgray'),
    text=all_callsigns,
    name='Planes'
))

# Path line
fig.add_trace(go.Scattergeo(
    lon = path_lons,
    lat = path_lats,
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
