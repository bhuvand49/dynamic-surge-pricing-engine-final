import h3

def get_zone(lat: float, lon: float) -> str:
    return h3.latlng_to_cell(lat, lon, 8)
