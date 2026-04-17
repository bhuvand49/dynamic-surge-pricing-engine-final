import time
import uuid
import sys
import os

# Add parent directory to path to fix ModuleNotFoundError
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from simulator.utils import generate_random_location
from simulator.geofence import get_zone
from simulator.redis_client import redis_client

print("[INFO] Rider simulation started...")

try:
    while True:
        rider_id = str(uuid.uuid4())
        lat, lon = generate_random_location()
        zone = get_zone(lat, lon)
        
        key = f"rider:{rider_id}"
        redis_client.hset(
            key,
            mapping={
                "lat": lat,
                "lon": lon,
                "zone": zone,
                "timestamp": time.time()
            }
        )
        # expire riders after 120s to simulate rider lifecycle and prevent infinite memory growth
        redis_client.expire(key, 120)
        
        time.sleep(3)
except KeyboardInterrupt:
    print("\n[STOP] Rider simulation stopped.")
    sys.exit(0)
