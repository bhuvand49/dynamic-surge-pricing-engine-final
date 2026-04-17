import random
from typing import Tuple

# Bangalore bounds
MIN_LAT, MAX_LAT = 12.85, 13.05
MIN_LON, MAX_LON = 77.45, 77.75


def generate_random_location() -> Tuple[float, float]:
    lat = random.uniform(MIN_LAT, MAX_LAT)
    lon = random.uniform(MIN_LON, MAX_LON)
    return lat, lon


def move_driver(lat: float, lon: float) -> Tuple[float, float]:
    lat += random.uniform(-0.0015, 0.0015)
    lon += random.uniform(-0.0015, 0.0015)
    
    # clamp coordinates to Bangalore bounds
    lat = max(MIN_LAT, min(lat, MAX_LAT))
    lon = max(MIN_LON, min(lon, MAX_LON))
    
    return lat, lon
