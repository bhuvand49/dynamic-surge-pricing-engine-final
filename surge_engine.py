import time
import random

from simulator.redis_client import redis_client
from ml.predictor import predict_surge, rule_based_surge

SURGE_INTERVAL = 4


def fetch_entities(prefix):
    rows = []

    for key in redis_client.scan_iter(f"{prefix}:*"):
        item = redis_client.hgetall(key)
        if item:
            rows.append(item)

    return rows


def group_by_zone(rows):
    result = {}

    for row in rows:
        zone = row.get("zone")
        if zone:
            result[zone] = result.get(zone, 0) + 1

    return result


def calculate(drivers, riders, zone):
    rule = rule_based_surge(drivers, riders)
    ml = predict_surge(drivers, riders, zone)

    final = (0.65 * rule) + (0.35 * ml)

    if riders > drivers:
        final += min((riders - drivers) * 0.08, 1.5)

    final += random.uniform(-0.05, 0.08)

    prev = redis_client.hget(f"surge:{zone}", "surge_multiplier")

    if prev:
        try:
            final = (0.65 * float(prev)) + (0.35 * final)
        except:
            pass

    final = max(1.0, min(final, 4.0))
    final = round(final, 2)

    return round(rule, 2), round(ml, 2), final


def run():
    print("[INFO] Surge engine started")

    while True:
        try:
            drivers = group_by_zone(fetch_entities("driver"))
            riders = group_by_zone(fetch_entities("rider"))

            zones = set(drivers.keys()) | set(riders.keys())

            for zone in zones:
                d = drivers.get(zone, 0)
                r = riders.get(zone, 0)

                rule, ml, surge = calculate(d, r, zone)

                redis_client.hset(
                    f"surge:{zone}",
                    mapping={
                        "drivers": d,
                        "riders": r,
                        "rule_surge": rule,
                        "ml_surge": ml,
                        "surge_multiplier": surge,
                        "timestamp": time.time()
                    }
                )

                redis_client.expire(f"surge:{zone}", 120)

            time.sleep(SURGE_INTERVAL)

        except Exception as e:
            print("Surge engine error:", e)
            time.sleep(3)


if __name__ == "__main__":
    run()