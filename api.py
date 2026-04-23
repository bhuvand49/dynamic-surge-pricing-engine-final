from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import threading
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

MIN_LAT, MAX_LAT = 12.85, 13.05
MIN_LON, MAX_LON = 77.45, 77.75
RESOLUTION = 7


@app.on_event("startup")
def startup_jobs():
    threading.Thread(target=run_driver_simulator, daemon=True).start()
    threading.Thread(target=run_rider_simulator, daemon=True).start()
    threading.Thread(target=run_surge_engine, daemon=True).start()
    print("[OK] Background jobs started")


@app.get("/")
def root():
    return {"message": "Dynamic Surge API Running 🚀"}


@app.get("/drivers")
def get_drivers():
    result = []
    for key in redis_client.scan_iter("driver:*"):
        row = redis_client.hgetall(key)
        if row:
            result.append({
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "zone": row["zone"]
            })
    return result


@app.get("/riders")
def get_riders():
    result = []
    for key in redis_client.scan_iter("rider:*"):
        row = redis_client.hgetall(key)
        if row:
            result.append({
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "zone": row["zone"]
            })
    return result


@app.get("/surge/all")
def get_all_surge():
    zones = []

    for key in redis_client.scan_iter("surge:*"):
        row = redis_client.hgetall(key)
        if not row:
            continue

        zone = key.replace("surge:", "")
        boundary = h3.cell_to_boundary(zone)
        polygon = [[lat, lon] for lat, lon in boundary]

        zones.append({
            "zone": zone,
            "area": zone[:8],
            "drivers": int(float(row.get("drivers", 0))),
            "riders": int(float(row.get("riders", 0))),
            "surge_multiplier": float(row.get("surge_multiplier", 1)),
            "polygons": [polygon]
        })

    return zones


@app.get("/grid")
def get_grid():
    cells = set()

    lat = MIN_LAT
    while lat <= MAX_LAT:
        lon = MIN_LON

        while lon <= MAX_LON:
            cells.add(h3.latlng_to_cell(lat, lon, RESOLUTION))
            lon += 0.01

        lat += 0.01   # ✅ correct place

    result = []

    for zone in cells:
        boundary = h3.cell_to_boundary(zone)
        polygon = [[lat, lon] for lat, lon in boundary]

        result.append({
            "zone": zone,
            "polygons": [polygon]
        })

    return result


@app.get("/scenario")
def get_scenario():
    return state


@app.post("/scenario")
def update_scenario(payload: dict = Body(...)):
    state["rain"] = int(payload.get("rain", 0))
    state["event"] = int(payload.get("event", 0))
    return {"message": "updated", "state": state}