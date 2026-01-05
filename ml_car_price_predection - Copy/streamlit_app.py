import streamlit as st
import pandas as pd
import requests
import streamlit as st
import pandas as pd
import requests
try:
    import shap
    HAS_SHAP = True
except Exception:
    shap = None
    HAS_SHAP = False
import joblib
import os
import matplotlib.pyplot as plt
from data import generate_synthetic_car_data, load_dataset

st.set_page_config(page_title="Car Price Explorer", layout="wide")

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "model.pkl")

st.title("Car Price Prediction Explorer")

if not os.path.exists(MODEL_PATH):
    st.warning("Model artifact not found. Run `python train.py` first to produce `models/model.pkl`.")
else:
    payload = joblib.load(MODEL_PATH)
    model = payload["model"]
    features = payload.get("features", [])

    # Show sample data: prefer actual CSV if present
    st.sidebar.header("Controls")
    n = st.sidebar.slider("Number of samples to preview", 50, 500, 200)
    try:
        df_full, target = load_dataset()
        df = df_full.head(n)
    except Exception:
        df = generate_synthetic_car_data(n)

    st.subheader("Sample Data")
    st.dataframe(df.head(50))

    st.subheader("Make a prediction (local API)")
    # helper: normalize names and find matching column in dataset
    def _norm(s: str) -> str:
        return "".join(c for c in s.lower() if c.isalnum()) if s else ""

    def find_col(*names):
        for n in names:
            nn = _norm(n)
            for col in df.columns:
                if _norm(col) == nn:
                    return col
        return None

    # map dataset columns to expected fields
    col_brand = find_col("brand", "make", "manufacturer")
    col_condition = find_col("condition", "vehiclecondition", "state")
    col_trans = find_col("transmission", "trans")
    col_year = find_col("year")
    col_mileage = find_col("mileage", "miles")
    col_engine = find_col("engine_size", "engine size", "engine")

    def uniq_sorted(col, numeric=False):
        if col is None or col not in df.columns:
            return [None]
        vals = df[col].dropna().unique().tolist()
        try:
            if numeric:
                vals = sorted([float(v) for v in vals])
            else:
                vals = sorted(vals)
        except Exception:
            vals = sorted(vals, key=lambda x: str(x))
        return vals

    brands = uniq_sorted(col_brand)
    conditions = uniq_sorted(col_condition)
    transmissions = uniq_sorted(col_trans)
    # Year selection: fixed range for broader coverage (1900-2026)
    years = list(range(1900, 2027))
    # Mileage selection: broad range from 100 to 2,000,000 (step 100 for usability)
    mileages = list(range(100, 2000001, 100))
    engines = uniq_sorted(col_engine, numeric=True)

    with st.form("predict_form"):
        year = st.selectbox("Year", options=years, index=0 if years else 0)
        mileage = st.selectbox("Mileage", options=mileages, index=0 if mileages else 0)
        engine_size = st.selectbox("Engine size (L)", options=engines, index=0 if engines else 0)
        brand = st.selectbox("Brand", options=brands, index=0 if brands else 0)
        condition = st.selectbox("Condition", options=conditions, index=0 if conditions else 0)
        transmission = st.selectbox("Transmission", options=transmissions, index=0 if transmissions else 0)
        submitted = st.form_submit_button("Predict via API")

    if submitted:
        # Call local API
        # Try a list of likely API endpoints so the UI works inside/outside Docker
        api_candidates = []
        if os.environ.get("API_URL"):
            api_candidates.append(os.environ.get("API_URL"))
        # Docker Desktop provides host.docker.internal to reach host from container
        api_candidates.extend([
            "http://host.docker.internal:8000",
            "http://car-price-api:8000",
            "http://127.0.0.1:8000",
        ])

        payload = {
            "year": int(year) if year is not None else None,
            "mileage": float(mileage) if mileage is not None else None,
            "brand": brand,
            "condition": condition,
            "engine_size": float(engine_size) if engine_size is not None else None,
            "transmission": transmission,
        }

        last_exc = None
        resp = None
        for base in api_candidates:
            if not base:
                continue
            url = base.rstrip("/") + "/predict"
            try:
                resp = requests.post(url, json=payload, timeout=5)
                if resp.status_code == 200:
                    break
                # record non-200 but keep trying other endpoints
                last_exc = Exception(f"HTTP {resp.status_code}: {resp.text}")
            except Exception as e:
                last_exc = e

        if resp is not None and resp.status_code == 200:
            st.success(f"Predicted price: ${resp.json().get('predicted_price'):.2f}")
        else:
            st.error(f"Error calling API: {last_exc}")

    st.subheader("SHAP Explainability")
    if st.button("Compute SHAP summary (may be slow)"):
        # compute SHAP using a small sample
        if not HAS_SHAP:
            st.error("The package 'shap' is not installed. Install with `pip install -r requirements.txt` or `pip install shap` and restart the app.")
        else:
            try:
                sample = df.copy() if df.shape[0] >= 50 else generate_synthetic_car_data(200)
                if "price" in sample.columns:
                    sample = sample.drop(columns=["price"], errors='ignore')
                X = pd.get_dummies(sample, columns=[c for c in ["brand", "condition", "transmission"] if c in sample.columns], drop_first=True)
                # align columns to model
                X = X.reindex(columns=features, fill_value=0)
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X)
                plt.clf()
                shap.summary_plot(shap_values, X, show=False)
                st.pyplot(plt.gcf())
            except Exception as e:
                st.error(f"Error computing SHAP: {e}")
