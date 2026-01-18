import math

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