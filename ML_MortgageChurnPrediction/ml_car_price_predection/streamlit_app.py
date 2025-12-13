import streamlit as st
import pandas as pd
import requests
import streamlit as st
import pandas as pd
import requests
import shap
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
    # attempt to get reasonable options from sample data
    brands = df["brand"].unique().tolist() if "brand" in df.columns else [None]
    conditions = df["condition"].unique().tolist() if "condition" in df.columns else [None]
    transmissions = df["transmission"].unique().tolist() if "transmission" in df.columns else [None]

    with st.form("predict_form"):
        year = st.number_input("Year", min_value=1980, max_value=2024, value=int(df["year"].iloc[0]) if "year" in df.columns else 2016)
        mileage = st.number_input("Mileage", min_value=0, max_value=1000000, value=int(df["mileage"].iloc[0]) if "mileage" in df.columns else 60000)
        brand = st.selectbox("Brand", options=brands)
        condition = st.selectbox("Condition", options=conditions)
        engine_size = st.number_input("Engine size (L)", min_value=0.8, max_value=6.0, value=float(df["engine_size"].iloc[0]) if "engine_size" in df.columns else 2.0, step=0.1)
        transmission = st.selectbox("Transmission", options=transmissions)
        submitted = st.form_submit_button("Predict via API")

    if submitted:
        # Call local API
        try:
            resp = requests.post("http://localhost:8000/predict", json={
                "year": int(year) if year is not None else None,
                "mileage": float(mileage) if mileage is not None else None,
                "brand": brand,
                "condition": condition,
                "engine_size": float(engine_size) if engine_size is not None else None,
                "transmission": transmission
            }, timeout=5)
            if resp.status_code == 200:
                st.success(f"Predicted price: ${resp.json()['predicted_price']:.2f}")
            else:
                st.error(f"API error: {resp.status_code} {resp.text}")
        except Exception as e:
            st.error(f"Error calling API: {e}")

    st.subheader("SHAP Explainability")
    if st.button("Compute SHAP summary (may be slow)"):
        # compute SHAP using a small sample
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
