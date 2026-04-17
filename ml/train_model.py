import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error

def main():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CSV_PATH = os.path.join(BASE_DIR, "surge_dataset.csv")
    MODEL_PATH = os.path.join(BASE_DIR, "ml", "surge_model.pkl")
    COLUMNS_PATH = os.path.join(BASE_DIR, "ml", "columns.pkl")

    if not os.path.exists(CSV_PATH):
        print("[ERROR] Dataset not found.")
        return

    df = pd.read_csv(CSV_PATH).dropna()

    if df.empty:
        print("[ERROR] Dataset empty.")
        return

    df = pd.get_dummies(df, columns=["zone"])

    X = df.drop(["timestamp", "surge"], axis=1)
    y = df["surge"]

    joblib.dump(list(X.columns), COLUMNS_PATH)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=250,
        max_depth=12,
        min_samples_split=2,
        random_state=42,
        n_jobs=-1
    )

    print("[INFO] Training model...")
    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    r2 = r2_score(y_test, preds)
    mae = mean_absolute_error(y_test, preds)

    print(f"[OK] R² Score: {r2:.4f}")
    print(f"[OK] MAE: {mae:.4f}")

    joblib.dump(model, MODEL_PATH)
    print("[SAVED] Model saved.")

if __name__ == "__main__":
    main()