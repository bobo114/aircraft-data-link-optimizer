import math
from src.calculate_path import extrapolate_position, haversine, los_distance, compute_los_path

def test_extrapolate_position_north():
    lat, lon = 0.0, 0.0
    v = 250.0  # m/s
    dt = 10.0  # seconds
    new_lat, new_lon = extrapolate_position(lat, lon, v, 0.0, dt)
    expected_lat = (v * dt) / 6371000 * (180 / math.pi)
    assert abs(new_lat - expected_lat) < 1e-5
    assert abs(new_lon) < 1e-6

def test_haversine_equator_degree():
    d = haversine(0, 0, 0, 1)
    # approximate meters per degree at equator
    assert abs(d - 111319.5) < 200

def test_los_distance_sum():
    h1 = 10000
    h2 = 0
    expected = math.sqrt(2 * 6371000 * h1) + math.sqrt(2 * 6371000 * h2)
    assert abs(los_distance(h1, h2) - expected) < 1e-6

def test_compute_los_path_two_hop():
    A = {"icao24": "A", "callsign": "A", "lat": 0.0, "lon": 0.0, "geo_alt": 100}
    B = {"icao24": "B", "callsign": "B", "lat": 0.0, "lon": 0.3, "geo_alt": 100}
    C = {"icao24": "C", "callsign": "C", "lat": 0.0, "lon": 0.9, "geo_alt": 100}
    path = compute_los_path([A, B, C], "A", "C")
    assert path is not None
    assert [p["icao24"] for p in path] == ["A", "B", "C"]

def test_compute_los_path_none():
    A = {"icao24": "A", "callsign": "A", "lat": 0.0, "lon": 0.0, "geo_alt": 10}
    B = {"icao24": "B", "callsign": "B", "lat": 0.0, "lon": 0.2, "geo_alt": 10}
    C = {"icao24": "C", "callsign": "C", "lat": 0.0, "lon": 2.0, "geo_alt": 10}
    path = compute_los_path([A, B, C], "A", "C")
    assert path is None
