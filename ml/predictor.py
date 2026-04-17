import os
import time
import joblib
import pandas as pd
from typing import Optional, Any

from .scenario_state import state

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "ml", "surge_model.pkl")
COLUMNS_PATH = os.path.join(BASE_DIR, "ml", "columns.pkl")

model: Optional[Any] = None
columns = None

try:
    model = joblib.load(MODEL_PATH)
    columns = joblib.load(COLUMNS_PATH)
    print("[OK] ML model loaded successfully")
except Exception as e:
    print(f"[WARN] ML not loaded: {e}")


def rule_based_surge(supply: int, demand: int) -> float:
    if supply <= 0:
        return 3.0

    ratio = demand / supply

    if ratio < 1:
        return 1.0
    elif ratio < 2:
        return 1.5
    elif ratio < 3:
        return 2.0
    else:
        return 3.0


def predict_surge(supply: int, demand: int, zone: str) -> float:
    if model is None or columns is None:
        return rule_based_surge(supply, demand)

    try:
        supply = max(supply, 1)
        ratio = demand / supply
        hour = time.localtime().tm_hour

        rain = int(state.get("rain", 0))
        event = int(state.get("event", 0))
        peak_hour = 1 if (7 <= hour <= 10 or 17 <= hour <= 21) else 0
        delay = 5 if rain else 0
        delay += 5 if event else 0

        input_dict = {
            "drivers": supply,
            "riders": demand,
            "ratio": ratio,
            "hour": hour,
            "rain": rain,
            "event": event,
            "peak_hour": peak_hour,
            "delay": delay
        }

        for col in columns:
            if col.startswith("zone_"):
                input_dict[col] = 0

        zone_col = f"zone_{zone}"
        if zone_col in input_dict:
            input_dict[zone_col] = 1

        df = pd.DataFrame([input_dict])
        df = df.reindex(columns=columns, fill_value=0)

        prediction = float(model.predict(df)[0])
        prediction = max(1.0, min(prediction, 4.0))

        return round(prediction, 2)

    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        return rule_based_surge(supply, demand)