import random
from typing import Tuple

MIN_LAT, MAX_LAT = 12.92, 13.01
MIN_LON, MAX_LON = 77.52, 77.69

HOTSPOTS = [
    (12.9716, 77.5946),  # Central Bengaluru
    (12.9352, 77.6245),  # Koramangala
    (12.9784, 77.6408),  # Indiranagar
    (12.9116, 77.6474),  # HSR
    (12.9860, 77.7060),  # Whitefield (adjusted inside bounds)
]

def generate_random_location() -> Tuple[float, float]:
    if random.random() < 0.85:
        base_lat, base_lon = random.choice(HOTSPOTS)
        lat = base_lat + random.uniform(-0.006, 0.006)
        lon = base_lon + random.uniform(-0.006, 0.006)
    else:
        lat = random.uniform(MIN_LAT, MAX_LAT)
        lon = random.uniform(MIN_LON, MAX_LON)

    lat = max(MIN_LAT, min(MAX_LAT, lat))
    lon = max(MIN_LON, min(MAX_LON, lon))
    return lat, lon


def move_driver(lat: float, lon: float):
    lat += random.uniform(-0.0010, 0.0010)
    lon += random.uniform(-0.0010, 0.0010)

    lat = max(MIN_LAT, min(MAX_LAT, lat))
    lon = max(MIN_LON, min(MAX_LON, lon))
    return lat, lon