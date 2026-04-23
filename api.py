from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import threading
import math
import h3

from simulator.redis_client import redis_client
from simulator.driver_simulator import run_driver_simulator
from simulator.rider_simulator import run_rider_simulator
from surge_engine import run as run_surge_engine
from ml.scenario_state import state

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MIN_LAT, MAX_LAT = 12.88, 13.04
MIN_LON, MAX_LON = 77.48, 77.74
RESOLUTION = 8

CITY_CENTER_LAT = 12.9716
CITY_CENTER_LON = 77.5946
CITY_RADIUS = 0.12


def inside_city(lat, lon):
    dist = math.sqrt(
        (lat - CITY_CENTER_LAT) ** 2 +
        (lon - CITY_CENTER_LON) ** 2
    )
    return dist <= CITY_RADIUS


def clear_old_data():
    for pattern in ["driver:*", "rider:*", "surge:*"]:
        for key in redis_client.scan_iter(pattern):
            redis_client.delete(key)


@app.on_event("startup")
def startup_jobs():
    clear_old_data()

    threading.Thread(target=run_driver_simulator, daemon=True).start()
    threading.Thread(target=run_rider_simulator, daemon=True).start()
    threading.Thread(target=run_surge_engine, daemon=True).start()


@app.get("/")
def root():
    return {"message": "Dynamic Surge API Running"}


@app.get("/drivers")
def drivers():
    out = []

    for key in redis_client.scan_iter("driver:*"):
        row = redis_client.hgetall(key)
        if not row:
            continue

        lat = float(row.get("lat", 0)) if isinstance(row, dict) else 0
        lon = float(row.get("lon", 0)) if isinstance(row, dict) else 0

        if inside_city(lat, lon):
            out.append({
                "lat": lat,
                "lon": lon,
                "zone": row.get("zone", "") if isinstance(row, dict) else ""
            })

    return out


@app.get("/riders")
def riders():
    out = []

    for key in redis_client.scan_iter("rider:*"):
        row = redis_client.hgetall(key)
        if not row:
            continue

        lat = float(row.get("lat", 0)) if isinstance(row, dict) else 0
        lon = float(row.get("lon", 0)) if isinstance(row, dict) else 0

        if inside_city(lat, lon):
            out.append({
                "lat": lat,
                "lon": lon,
                "zone": row.get("zone", "") if isinstance(row, dict) else ""
            })

    return out


@app.get("/surge/all")
def surge_all():
    out = []

    for key in redis_client.scan_iter("surge:*"):
        row = redis_client.hgetall(key)
        if not row:
            continue

        zone = key.replace("surge:", "")

        try:
            lat, lon = h3.cell_to_latlng(zone)

            if not inside_city(lat, lon):
                continue

            poly = [[a, b] for a, b in h3.cell_to_boundary(zone)]

            if isinstance(row, dict):
                out.append({
                    "zone": zone,
                    "area": zone[:8],
                    "drivers": int(float(row.get("drivers", 0))),
                    "riders": int(float(row.get("riders", 0))),
                    "rule_surge": float(row.get("rule_surge", 1)),
                    "ml_surge": float(row.get("ml_surge", 1)),
                    "surge_multiplier": float(row.get("surge_multiplier", 1)),
                    "polygons": [poly]
                })
        except:
            pass

    return out


@app.get("/grid")
def grid():
    cells = set()

    lat = MIN_LAT
    while lat <= MAX_LAT:
        lon = MIN_LON
        while lon <= MAX_LON:
            if inside_city(lat, lon):
                cells.add(h3.latlng_to_cell(lat, lon, RESOLUTION))
            lon += 0.004
        lat += 0.004

    out = []

    for cell in cells:
        try:
            poly = [[a, b] for a, b in h3.cell_to_boundary(cell)]
            out.append({"zone": cell, "polygons": [poly]})
        except:
            pass

    return out


@app.get("/scenario")
def scenario():
    return state


@app.post("/scenario")
def scenario_update(payload: dict = Body(...)):
    state["rain"] = int(payload.get("rain", 0))
    state["event"] = int(payload.get("event", 0))
    return state