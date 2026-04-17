import sys
import os
import time
import csv
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from simulator.redis_client import redis_client

FILE = os.path.join(BASE_DIR, "surge_dataset.csv")

if not os.path.exists(FILE):
    with open(FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "zone",
            "drivers",
            "riders",
            "ratio",
            "hour",
            "rain",
            "event",
            "peak_hour",
            "delay",
            "surge"
        ])

print("[INFO] Realistic ML data collector started...")

try:
    while True:
        keys = list(redis_client.scan_iter("surge:*"))

        for key in keys:
            key_str = key.decode() if isinstance(key, bytes) else key
            parts = key_str.split(":")
            if len(parts) < 2:
                continue

            zone = parts[1]
            raw = redis_client.hgetall(key_str)

            if not raw:
                continue

            drivers = int(raw.get("drivers", 0))
            riders = int(raw.get("riders", 0))

            ratio = riders / max(drivers, 1)
            hour = time.localtime().tm_hour

            # Hidden factors
            rain = random.choice([0, 1])
            event = random.choice([0, 1])
            peak_hour = 1 if (7 <= hour <= 10 or 17 <= hour <= 21) else 0
            delay = random.randint(0, 15)

            # Realistic target generation
            surge = 1.0
            surge += ratio * 0.35
            surge += 0.4 if rain else 0
            surge += 0.5 if event else 0
            surge += 0.3 if peak_hour else 0
            surge += delay * 0.03
            surge += random.uniform(-0.15, 0.15)

            surge = round(max(1.0, min(surge, 4.0)), 2)

            with open(FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    time.time(),
                    zone,
                    drivers,
                    riders,
                    ratio,
                    hour,
                    rain,
                    event,
                    peak_hour,
                    delay,
                    surge
                ])

        time.sleep(5)

except KeyboardInterrupt:
    print("\n[STOP] Collector stopped.")
    sys.exit(0)