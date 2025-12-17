"""
FastAPI prediction service. Loads the trained model from `models/model.pkl`.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Tuple
import joblib
import pandas as pd
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "model.pkl")

app = FastAPI(title="Car Price Prediction API")


class PredictRequest(BaseModel):
    year: Optional[int] = None
    mileage: Optional[float] = None
    brand: Optional[str] = None
    condition: Optional[str] = None
    engine_size: Optional[float] = None
    transmission: Optional[str] = None


def load_model() -> Tuple[object, List[str], Optional[str]]:
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Model not found at {MODEL_PATH}. Run train.py first.")
    payload = joblib.load(MODEL_PATH)
    model = payload.get("model")
    features = payload.get("features", [])
    target = payload.get("target")
    return model, features, target


model, feature_columns, target_col = load_model()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/info")
def info():
    return {"n_features": len(feature_columns), "features": feature_columns, "target": target_col}


@app.post("/predict")
def predict(req: PredictRequest):
    # build a zero-initialized row with the expected feature columns
    X = pd.DataFrame([{c: 0 for c in feature_columns}])

    # map known numeric inputs
    if req.year is not None and "year" in X.columns:
        X.at[0, "year"] = req.year
    if req.mileage is not None and "mileage" in X.columns:
        X.at[0, "mileage"] = req.mileage
    if req.engine_size is not None and "engine_size" in X.columns:
        X.at[0, "engine_size"] = req.engine_size

    # set one-hot columns for categorical inputs
    if req.brand:
        col = f"brand_{req.brand}"
        if col in X.columns:
            X.at[0, col] = 1
    if req.condition:
        col = f"condition_{req.condition}"
        if col in X.columns:
            X.at[0, col] = 1
    if req.transmission:
        col = f"transmission_{req.transmission}"
        if col in X.columns:
            X.at[0, col] = 1

    # ensure numeric dtype
    for c in X.columns:
        try:
            X[c] = pd.to_numeric(X[c])
        except Exception:
            pass

    pred = model.predict(X)[0]
    return {"predicted_price": float(pred)}
