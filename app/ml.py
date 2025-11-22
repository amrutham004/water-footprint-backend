# app/ml.py
import os
import joblib
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

MODEL_PATH = os.path.join(DATA_DIR, "model.pkl")
X_COLS_PATH = os.path.join(DATA_DIR, "X_columns.pkl")
PRIMARY_CATEGORIES_PATH = os.path.join(DATA_DIR, "primary_categories.pkl")

# Try to load a real model; if missing, create a small dummy model for demo.
def _ensure_model_exists():
    if os.path.exists(MODEL_PATH) and os.path.exists(X_COLS_PATH):
        return

    # create a tiny synthetic dataset and train a trivial sklearn DummyRegressor
    print("No model found — creating a demo dummy model for immediate testing.")
    from sklearn.dummy import DummyRegressor
    # Synthetic features used in this demo
    X_columns = ["Usage_Hours","Family_Size","Appliances","Primary_Appliance",
                 "Water_Saving_Device","Water_Usage_Per_Capita","Usage_X_Appliances"]
    # Create a small dataset (10 rows)
    rng = np.random.RandomState(0)
    X = pd.DataFrame({
        "Usage_Hours": rng.uniform(1,8,10),
        "Family_Size": rng.randint(1,6,10),
        "Appliances": rng.randint(1,6,10),
        "Primary_Appliance": rng.randint(0,4,10),
        "Water_Saving_Device": rng.randint(0,2,10),
        "Water_Usage_Per_Capita": rng.uniform(10,100,10),
        "Usage_X_Appliances": rng.uniform(1,50,10),
    })
    # Target is synthetic (not meaningful) but allows predict()
    y = (X["Usage_Hours"] * 10 + X["Family_Size"] * 5 + X["Appliances"] * 2).values
    model = DummyRegressor(strategy="mean")
    model.fit(X, y)

    # Save model and X columns
    joblib.dump(model, MODEL_PATH)
    joblib.dump(X_columns, X_COLS_PATH)
    # Save a simple primary categories list for encoding (demo)
    primary_categories = ["Sink", "Shower", "Toilet", "Washing Machine"]
    joblib.dump(primary_categories, PRIMARY_CATEGORIES_PATH)

# Ensure model exists on import
_ensure_model_exists()

# Load model and metadata
model = joblib.load(MODEL_PATH)
X_COLUMNS = joblib.load(X_COLS_PATH)
try:
    primary_categories = joblib.load(PRIMARY_CATEGORIES_PATH)
except Exception:
    primary_categories = ["Sink", "Shower", "Toilet", "Washing Machine"]

primary_to_code = {cat.lower(): i for i, cat in enumerate(primary_categories)}

def _encode_primary(appliance: str):
    if appliance is None:
        return 0
    key = str(appliance).strip().lower()
    return primary_to_code.get(key, 0)

def prepare_features(family_size, usage_hours, appliances, primary_appliance, water_saving_device):
    # Basic feature engineering used by training script earlier:
    usage_hours = float(usage_hours) if usage_hours is not None else 0.0
    family_size = int(family_size) if family_size is not None else 1
    appliances = int(appliances) if appliances is not None else 1
    primary_encoded = _encode_primary(primary_appliance)
    device_encoded = 1 if str(water_saving_device).lower() in ("1","true","yes","y") else 0
    usage_x_appliances = usage_hours * appliances
    water_usage_per_capita = 0.0  # placeholder; if your training used it, supply real calc

    # Build DataFrame respecting X_COLUMNS order
    values = {
        "Usage_Hours": usage_hours,
        "Family_Size": family_size,
        "Appliances": appliances,
        "Primary_Appliance": primary_encoded,
        "Water_Saving_Device": device_encoded,
        "Water_Usage_Per_Capita": water_usage_per_capita,
        "Usage_X_Appliances": usage_x_appliances
    }
    X = pd.DataFrame([[values[c] for c in X_COLUMNS]], columns=X_COLUMNS)
    return X

def predict_water_usage(family_size, usage_hours, appliances, primary_appliance, water_saving_device):
    X = prepare_features(family_size, usage_hours, appliances, primary_appliance, water_saving_device)
    pred = float(model.predict(X)[0])
    # compute counterfactual (no device) if device present
    if str(water_saving_device).lower() in ("1","true","yes","y"):
        X_no = X.copy()
        if "Water_Saving_Device" in X_no.columns:
            X_no["Water_Saving_Device"] = 0
        pred_no = float(model.predict(X_no)[0])
        savings = pred_no - pred
    else:
        savings = 0.0
    return pred, savings
