import math
import heapq
from collections import deque

def extrapolate_position(lat, lon, velocity, track, time_delta_seconds):
    """
    Calculates new lat/lon based on velocity (m/s) and true track (degrees).
    Uses a simple flat-earth approximation suitable for short time intervals.
    """
    if velocity is None or track is None:
        return lat, lon

    # Earth radius in meters
    R = 6371000
    
    # Distance traveled in meters
    distance = velocity * time_delta_seconds
    
    # Convert track to radians
    track_rad = math.radians(track)
    
    # Calculate displacement in meters
    delta_n = distance * math.cos(track_rad)
    delta_e = distance * math.sin(track_rad)
    
    # Convert displacements to lat/lon changes
    new_lat = lat + (delta_n / R) * (180 / math.pi)
    new_lon = lon + (delta_e / (R * math.cos(math.radians(lat)))) * (180 / math.pi)
    
    return new_lat, new_lon

# ---------------------------
# Helper functions
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
# Dijkstra shortest path
# ---------------------------
def dijkstra(graph, start_id, end_id):
    queue = [(0, start_id, [])]
    seen = set()
    while queue:
        total, node, path = heapq.heappop(queue)
        if node == end_id:
            return path + [node]
        if node in seen:
            continue
        seen.add(node)
        for neighbor, delay in graph.get(node, []):
            if neighbor not in seen:
                heapq.heappush(queue, (total + delay, neighbor, path + [node]))
    return None

# ---------------------------
# BFS for hop-minimizing
# ---------------------------
def bfs_shortest_hops(graph, start_id, end_id):
    """
    Return path (list of node ids) minimizing number of hops (BFS).
    graph: adjacency list mapping id -> list of (neighbor_id, weight)
    """
    q = deque([[start_id]])
    visited = {start_id}
    while q:
        path = q.popleft()
        node = path[-1]
        if node == end_id:
            return path
        for neighbor, _ in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                q.append(path + [neighbor])
    return None

# ---------------------------
# Main path function
# ---------------------------
def compute_los_path(planes_list, start_icao, end_icao, extra_delay=0.0, metric='delay'):
    """
    planes_list: list of dicts, each with keys ['icao24','callsign','lat','lon','geo_alt']
    start_icao: ICAO24 of start plane (already in planes_list)
    end_icao: ICAO24 of end plane (already in planes_list)
    extra_delay: float, extra constant added to each link delay
    metric: 'delay' (default) to minimize estimated transmission delay (Dijkstra),
            'hops' to minimize number of relays (BFS / unit weights)

    Returns: list of dicts representing the path from start to end
    """
    nodes = planes_list  # start/end are already included

    # Build graph: adjacency list by LOS
    graph = {p['icao24']: [] for p in nodes}
    for i, p1 in enumerate(nodes):
        for j, p2 in enumerate(nodes):
            if i >= j:
                continue
            d = haversine(p1['lat'], p1['lon'], p2['lat'], p2['lon'])
            max_los = los_distance(p1.get('geo_alt', 0), p2.get('geo_alt', 0))
            if d <= max_los:
                if metric == 'hops':
                    weight = 1.0
                else:
                    weight = d / 300000 + extra_delay
                graph[p1['icao24']].append((p2['icao24'], weight))
                graph[p2['icao24']].append((p1['icao24'], weight))

    # Compute path as list of icao24 IDs
    if metric == 'hops':
        path_ids = bfs_shortest_hops(graph, start_icao, end_icao)
    else:
        path_ids = dijkstra(graph, start_icao, end_icao)

    if path_ids is None:
        return None

    # Convert path IDs to full node dicts
    id_to_node = {p['icao24']: p for p in nodes}
    path_nodes = [id_to_node[icao] for icao in path_ids]

    return path_nodes
