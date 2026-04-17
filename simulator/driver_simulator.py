import time
import uuid
import sys
import os

# Add parent directory to path to fix ModuleNotFoundError
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from simulator.utils import generate_random_location, move_driver
from simulator.geofence import get_zone
from simulator.redis_client import redis_client

drivers = {}

# create initial drivers
for _ in range(300):
    driver_id = str(uuid.uuid4())
    lat, lon = generate_random_location()
    drivers[driver_id] = {"lat": lat, "lon": lon}

print("[INFO] Driver simulation started...")

try:
    while True:
        for driver_id in drivers:
            lat = drivers[driver_id]["lat"]
            lon = drivers[driver_id]["lon"]
            
            lat, lon = move_driver(lat, lon)
            zone = get_zone(lat, lon)
            
            drivers[driver_id]["lat"] = lat
            drivers[driver_id]["lon"] = lon
            
            key = f"driver:{driver_id}"
            redis_client.hset(
                key,
                mapping={
                    "lat": lat,
                    "lon": lon,
                    "zone": zone,
                    "timestamp": time.time()
                }
            )
            # expire driver after 60s of inactivity to avoid ghost drivers
            redis_client.expire(key, 60)
            
        print("Drivers updated", flush=True)
        time.sleep(2)
except KeyboardInterrupt:
    print("\n[STOP] Driver simulation stopped.")
    sys.exit(0)
