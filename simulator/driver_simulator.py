import time
import uuid
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from simulator.utils import generate_random_location, move_driver
from simulator.geofence import get_zone
from simulator.redis_client import redis_client


def run_driver_simulator():
    drivers = {}
    print("[INFO] Driver simulator started")

    while True:
        try:
            # keep max 45 active drivers
            if len(drivers) < 45:
                driver_id = str(uuid.uuid4())
                lat, lon = generate_random_location()
                drivers[driver_id] = {"lat": lat, "lon": lon}

            for did in list(drivers.keys()):
                lat = drivers[did]["lat"]
                lon = drivers[did]["lon"]

                lat, lon = move_driver(lat, lon)
                zone = get_zone(lat, lon)

                drivers[did]["lat"] = lat
                drivers[did]["lon"] = lon

                redis_client.hset(
                    f"driver:{did}",
                    mapping={
                        "lat": lat,
                        "lon": lon,
                        "zone": zone,
                        "timestamp": time.time()
                    }
                )

                redis_client.expire(f"driver:{did}", 180)

            time.sleep(2)

        except Exception as e:
            print("Driver simulator error:", e)
            time.sleep(2)


if __name__ == "__main__":
    run_driver_simulator()