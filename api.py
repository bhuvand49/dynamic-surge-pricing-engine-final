from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from simulator.redis_client import redis_client
from simulator.geofence import get_zone
from ml.scenario_state import state
from typing import Dict, Any, List
import h3

app = FastAPI()

# ---------------------------------
# CORS
# ---------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------
# ROOT
# ---------------------------------
@app.get("/")
def root():
    return {"message": "Dynamic Surge API Running 🚀"}

# ---------------------------------
# DEEP BANGALORE LOCALITY MAP
# ---------------------------------
LOCALITIES = [
    ("MG Road", 12.9756, 77.6050),
    ("Indiranagar", 12.9784, 77.6408),
    ("Koramangala", 12.9352, 77.6245),
    ("Whitefield", 12.9698, 77.7500),
    ("Electronic City", 12.8399, 77.6770),
    ("Jayanagar", 12.9293, 77.5828),
    ("Hebbal", 13.0358, 77.5970),
    ("Yelahanka", 13.1007, 77.5963),
    ("Marathahalli", 12.9591, 77.6974),
    ("HSR Layout", 12.9116, 77.6474),
    ("BTM Layout", 12.9166, 77.6101),
    ("Banashankari", 12.9255, 77.5468),
    ("Rajajinagar", 12.9915, 77.5544),
    ("Malleshwaram", 13.0035, 77.5706),
    ("Airport Zone", 13.1986, 77.7066),
]

def distance(lat1, lon1, lat2, lon2):
    return ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5

def get_area_name(zone: str):
    try:
        lat, lon = h3.cell_to_latlng(zone)

        best_name = "Unknown Area"
        best_dist = float("inf")

        for name, a_lat, a_lon in LOCALITIES:
            d = distance(lat, lon, a_lat, a_lon)
            if d < best_dist:
                best_dist = d
                best_name = name

        return best_name

    except Exception:
        return "Unknown Area"

# ---------------------------------
# SCENARIO CONTROL
# ---------------------------------
@app.get("/scenario")
def get_scenario():
    return state

@app.post("/scenario")
def update_scenario(data: dict = Body(...)):
    state["rain"] = int(data.get("rain", 0))
    state["event"] = int(data.get("event", 0))
    return {
        "message": "Scenario Updated",
        "state": state
    }

# ---------------------------------
# SINGLE SURGE BY LAT/LON
# ---------------------------------
@app.get("/surge")
def get_surge(lat: float, lon: float):

    zone = get_zone(lat, lon)
    raw = redis_client.hgetall(f"surge:{zone}")

    if not raw:
        return {
            "zone": zone,
            "area": get_area_name(zone),
            "drivers": 0,
            "riders": 0,
            "rule_surge": 1.0,
            "ml_surge": 1.0,
            "surge_multiplier": 1.0
        }

    return {
        "zone": zone,
        "area": get_area_name(zone),
        "drivers": int(raw.get("drivers", 0)),
        "riders": int(raw.get("riders", 0)),
        "rule_surge": float(raw.get("rule_surge", 1.0)),
        "ml_surge": float(raw.get("ml_surge", 1.0)),
        "surge_multiplier": float(raw.get("surge_multiplier", 1.0))
    }

# ---------------------------------
# GROUPED SURGE REGIONS (ONE CARD PER AREA)
# ---------------------------------
@app.get("/surge/all")
def get_all_surges():

    keys = list(redis_client.scan_iter("surge:*"))
    grouped = {}

    for key in keys:
        key_str = key.decode() if isinstance(key, bytes) else key
        zone = key_str.split(":")[1]

        raw = redis_client.hgetall(key_str)
        if not raw:
            continue

        area = get_area_name(zone)

        if area not in grouped:
            grouped[area] = {
                "count": 0,
                "drivers": 0,
                "riders": 0,
                "rule_surge": 0.0,
                "ml_surge": 0.0,
                "surge_multiplier": 0.0,
                "polygon": []
            }

        boundary = h3.cell_to_boundary(zone)

        grouped[area]["count"] += 1
        grouped[area]["drivers"] += int(raw.get("drivers", 0))
        grouped[area]["riders"] += int(raw.get("riders", 0))
        grouped[area]["rule_surge"] += float(raw.get("rule_surge", 1.0))
        grouped[area]["ml_surge"] += float(raw.get("ml_surge", 1.0))
        grouped[area]["surge_multiplier"] += float(raw.get("surge_multiplier", 1.0))
        grouped[area]["polygon"].append([[lat, lon] for lat, lon in boundary])

    results = []

    for area, data in grouped.items():
        c = data["count"]

        results.append({
            "region_id": area,
            "area": area,
            "drivers": data["drivers"],
            "riders": data["riders"],
            "rule_surge": round(data["rule_surge"] / c, 2),
            "ml_surge": round(data["ml_surge"] / c, 2),
            "surge_multiplier": round(data["surge_multiplier"] / c, 2),
            "polygons": data["polygon"]
        })

    return results

# ---------------------------------
# LIVE DRIVERS
# ---------------------------------
@app.get("/drivers")
def get_drivers():

    drivers = []
    keys = list(redis_client.scan_iter("driver:*"))

    for key in keys:
        raw = redis_client.hgetall(key)
        if not raw:
            continue

        drivers.append({
            "lat": float(raw.get("lat", 0)),
            "lon": float(raw.get("lon", 0)),
            "zone": raw.get("zone")
        })

    return drivers