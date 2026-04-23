import random
from typing import Tuple
from matplotlib.path import Path

# Same Bengaluru boundary as api.py
BENGALURU_BOUNDARY = [
    (12.835, 77.460),
    (12.870, 77.430),
    (12.930, 77.420),
    (13.000, 77.430),
    (13.060, 77.455),
    (13.105, 77.500),
    (13.120, 77.565),
    (13.115, 77.635),
    (13.095, 77.705),
    (13.050, 77.760),
    (12.995, 77.790),
    (12.930, 77.800),
    (12.875, 77.785),
    (12.835, 77.745),
    (12.810, 77.690),
    (12.800, 77.620),
    (12.805, 77.550),
    (12.820, 77.500),
]

city_path = Path(BENGALURU_BOUNDARY)

HOTSPOTS = [
    (12.9716, 77.5946),  # Central
    (12.9352, 77.6245),  # Koramangala
    (12.9784, 77.6408),  # Indiranagar
    (12.9116, 77.6474),  # HSR
    (12.9860, 77.7060),  # Whitefield
]

def inside_city(lat, lon):
    return city_path.contains_point((lat, lon))


def generate_random_location() -> Tuple[float, float]:
    while True:
        if random.random() < 0.85:
            base_lat, base_lon = random.choice(HOTSPOTS)
            lat = base_lat + random.uniform(-0.008, 0.008)
            lon = base_lon + random.uniform(-0.008, 0.008)
        else:
            lat = random.uniform(12.80, 13.12)
            lon = random.uniform(77.42, 77.80)

        if inside_city(lat, lon):
            return lat, lon


def move_driver(lat: float, lon: float):
    for _ in range(10):
        nlat = lat + random.uniform(-0.0012, 0.0012)
        nlon = lon + random.uniform(-0.0012, 0.0012)

        if inside_city(nlat, nlon):
            return nlat, nlon

    return lat, lon