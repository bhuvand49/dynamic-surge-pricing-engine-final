from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import threading
import h3
from matplotlib.path import Path

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

RESOLUTION = 8

# Realistic Bengaluru boundary
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


def inside_city(lat, lon):
    return city_path.contains_point((lat, lon))


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
        if row:
            lat = float(row["lat"])
            lon = float(row["lon"])
            if inside_city(lat, lon):
                out.append({
                    "lat": lat,
                    "lon": lon,
                    "zone": row["zone"]
                })
    return out


@app.get("/riders")
def riders():
    out = []
    for key in redis_client.scan_iter("rider:*"):
        row = redis_client.hgetall(key)
        if row:
            lat = float(row["lat"])
            lon = float(row["lon"])
            if inside_city(lat, lon):
                out.append({
                    "lat": lat,
                    "lon": lon,
                    "zone": row["zone"]
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

    lat = 12.79
    while lat <= 13.13:
        lon = 77.40
        while lon <= 77.82:
            if inside_city(lat, lon):
                cells.add(h3.latlng_to_cell(lat, lon, RESOLUTION))
            lon += 0.0028
        lat += 0.0028

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