import random
from typing import Tuple

MIN_LAT, MAX_LAT = 12.70, 13.20
MIN_LON, MAX_LON = 77.30, 77.85

HOTSPOTS = [
    (12.9756, 77.6050),   # MG Road
    (12.9352, 77.6245),   # Koramangala
    (12.9784, 77.6408),   # Indiranagar
    (12.9116, 77.6474),   # HSR
    (12.9698, 77.7500),   # Whitefield
]


def generate_random_location():
    if random.random() < 0.55:
        base_lat, base_lon = random.choice(HOTSPOTS)
        lat = base_lat + random.uniform(-0.015, 0.015)
        lon = base_lon + random.uniform(-0.015, 0.015)
    else:
        lat = random.uniform(MIN_LAT, MAX_LAT)
        lon = random.uniform(MIN_LON, MAX_LON)

    lat = max(MIN_LAT, min(lat, MAX_LAT))
    lon = max(MIN_LON, min(lon, MAX_LON))
    return lat, lon


def move_driver(lat, lon):
    lat += random.uniform(-0.002, 0.002)
    lon += random.uniform(-0.002, 0.002)

    lat = max(MIN_LAT, min(lat, MAX_LAT))
    lon = max(MIN_LON, min(lon, MAX_LON))

    return lat, lon