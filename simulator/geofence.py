import h3

RESOLUTION = 8

def get_zone(lat: float, lon: float) -> str:
    return h3.latlng_to_cell(lat, lon, RESOLUTION)