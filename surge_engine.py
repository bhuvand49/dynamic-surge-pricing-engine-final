import time
import sys
from typing import List, Dict, Any

from simulator.redis_client import redis_client
from ml.predictor import predict_surge, rule_based_surge

SURGE_INTERVAL = 8


# -----------------------------
# HYBRID SURGE (RULE + ML)
# -----------------------------
def calculate_surge(drivers: int, riders: int, zone: str):
    rule = rule_based_surge(drivers, riders)
    ml = predict_surge(drivers, riders, zone)

    # Weighted hybrid
    final = (0.7 * rule) + (0.3 * ml)

    # Optional smoothing (prevents flicker)
    prev_key = f"surge:{zone}"
    prev = redis_client.hget(prev_key, "surge_multiplier")

    if prev is not None:
        try:
            prev_str = prev.decode() if isinstance(prev, bytes) else str(prev)
            prev_val = float(prev_str)
            final = (0.7 * prev_val) + (0.3 * final)
        except (Exception, TypeError, ValueError):
            pass

    final = round(max(1.0, min(final, 4.0)), 2)

    return round(rule, 2), round(ml, 2), final


# -----------------------------
# REDIS HELPERS
# -----------------------------
def fetch_entities(prefix: str) -> List[Dict[str, Any]]:
    keys = list(redis_client.scan_iter(f"{prefix}:*"))
    data: List[Dict[str, Any]] = []

    for key in keys:
        key_str = key.decode() if isinstance(key, bytes) else key
        obj = redis_client.hgetall(key_str)

        if isinstance(obj, dict):
            decoded = {
                (k.decode() if isinstance(k, bytes) else k):
                (v.decode() if isinstance(v, bytes) else v)
                for k, v in obj.items()
            }
            data.append(decoded)

    return data


def group_by_zone(entities: List[Dict[str, Any]]) -> Dict[str, int]:
    zone_counts: Dict[str, int] = {}

    for entity in entities:
        zone = entity.get("zone")
        if zone is not None:
            z = str(zone)
            zone_counts[z] = zone_counts.get(z, 0) + 1

    return zone_counts


# -----------------------------
# MAIN ENGINE LOOP
# -----------------------------
def run_surge_engine() -> None:
    print("[INFO] Final Hybrid Surge engine running...")

    try:
        while True:
            drivers = fetch_entities("driver")
            riders = fetch_entities("rider")

            driver_zones = group_by_zone(drivers)
            rider_zones = group_by_zone(riders)

            all_zones = set(driver_zones.keys()).union(rider_zones.keys())

            for zone in all_zones:
                supply = driver_zones.get(zone, 0)
                demand = rider_zones.get(zone, 0)

                rule, ml, final = calculate_surge(supply, demand, zone)

                print(
                    f"[ZONE {zone}] "
                    f"D:{supply} R:{demand} | "
                    f"Rule:{rule} ML:{ml} Final:{final}"
                )

                key = f"surge:{zone}"

                redis_client.hset(
                    key,
                    mapping={
                        "drivers": supply,
                        "riders": demand,
                        "rule_surge": rule,
                        "ml_surge": ml,
                        "surge_multiplier": final,
                        "timestamp": time.time(),
                    }
                )

                redis_client.expire(key, 120)

            time.sleep(SURGE_INTERVAL)

    except KeyboardInterrupt:
        print("\n[STOP] Surge engine stopped.")
        sys.exit(0)


if __name__ == "__main__":
    run_surge_engine()