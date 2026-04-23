import time
import uuid
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from simulator.utils import generate_random_location
from simulator.geofence import get_zone
from simulator.redis_client import redis_client


def run_rider_simulator():
    print("[INFO] Rider simulator started")

    while True:
        try:
            # add 3 riders every cycle
            for _ in range(3):
                rider_id = str(uuid.uuid4())

                lat, lon = generate_random_location()
                zone = get_zone(lat, lon)

                redis_client.hset(
                    f"rider:{rider_id}",
                    mapping={
                        "lat": lat,
                        "lon": lon,
                        "zone": zone,
                        "timestamp": time.time()
                    }
                )
                redis_client.expire(f"rider:{rider_id}", 180)

            time.sleep(2)

        except Exception as e:
            print("Rider simulator error:", e)
            time.sleep(2)


if __name__ == "__main__":
    run_rider_simulator()