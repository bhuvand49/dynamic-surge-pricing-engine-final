import h3

HEX_RESOLUTION = 7

def get_zone(lat: float, lon: float) -> str:
    return h3.latlng_to_cell(lat, lon, HEX_RESOLUTION)