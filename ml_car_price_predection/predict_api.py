"""
FastAPI prediction service. Loads the trained model from database (preferred) or filesystem.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Tuple
import pandas as pd
import os
import sys
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.model_loader import load_production_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Car Price Prediction API")


class PredictRequest(BaseModel):
    year: Optional[int] = None
    mileage: Optional[float] = None
    brand: Optional[str] = None
    condition: Optional[str] = None
    engine_size: Optional[float] = None
    transmission: Optional[str] = None


def load_model() -> Tuple[object, object, object, List[str], Optional[str]]:
    """Load model from database (preferred) or filesystem"""
    try:
        model_artifact = load_production_model()
        if model_artifact:
            model = model_artifact.get("model")
            preprocessor = model_artifact.get("preprocessor")
            scaler = model_artifact.get("scaler")
            input_features = model_artifact.get("input_features", model_artifact.get("features", []))
            target = model_artifact.get("target")
            logger.info("✓ Model loaded successfully (from database or filesystem)")
            return model, preprocessor, scaler, input_features, target
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
    
    # If both database and filesystem fail, return empty placeholders
    logger.warning("No model found. API will start but predictions will fail.")
    return None, None, None, [], None


model, preprocessor, scaler, input_features, target_col = load_model()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/info")
def info():
    if model is None:
        return {"error": "Model not loaded. Run training and ensure models/model.pkl exists."}
    return {"n_features": len(input_features), "features": input_features, "target": target_col}


@app.post("/predict")
def predict(req: PredictRequest):
    # build a single-row raw input using the original input feature names
    if not input_features:
        return {"error": "Model input feature list is empty; check model artifact."}

    X_raw = pd.DataFrame([{c: None for c in input_features}])

    # map known numeric inputs
    # helper to normalize names and find matching column in input_features
    def _norm(s: str) -> str:
        return "".join([c for c in s.lower() if c.isalnum()]) if s else ""

    def find_col(*names):
        for n in names:
            nn = _norm(n)
            for col in input_features:
                if _norm(col) == nn:
                    return col
        return None

    # map numeric fields with flexible column names
    col_year = find_col("year", "Year")
    if req.year is not None and col_year is not None:
        X_raw.at[0, col_year] = req.year

    col_mileage = find_col("mileage", "miles", "Mileage")
    if req.mileage is not None and col_mileage is not None:
        X_raw.at[0, col_mileage] = req.mileage

    col_engine = find_col("engine_size", "engine size", "engine")
    if req.engine_size is not None and col_engine is not None:
        X_raw.at[0, col_engine] = req.engine_size

    # categorical fields
    col_brand = find_col("brand", "make", "manufacturer")
    if req.brand is not None and col_brand is not None:
        X_raw.at[0, col_brand] = req.brand

    col_condition = find_col("condition", "vehiclecondition", "state")
    if req.condition is not None and col_condition is not None:
        X_raw.at[0, col_condition] = req.condition

    col_trans = find_col("transmission", "trans")
    if req.transmission is not None and col_trans is not None:
        X_raw.at[0, col_trans] = req.transmission

    # Transform with saved preprocessor and scaler before predicting
    try:
        if preprocessor is not None:
            X_proc = preprocessor.transform(X_raw)
        else:
            X_proc = X_raw.values

        if scaler is not None:
            X_proc = scaler.transform(X_proc)

        pred = model.predict(X_proc)[0]
    except Exception as e:
        return {"error": f"Model prediction failed: {e}", "input_row": X_raw.iloc[0].to_dict()}

    return {"predicted_price": float(pred), "input_row": X_raw.iloc[0].to_dict()}
