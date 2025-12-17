"""
Synthetic car price data generator and simple feature engineering.
"""
"""
Synthetic car price data loader and simple feature engineering helpers.
This module will try to load an attached CSV (Car_Price_Prediction.csv) if present
and fall back to a synthetic generator otherwise.
"""
import numpy as np
import pandas as pd
import os
import re
from typing import Optional, Tuple


def generate_synthetic_car_data(n_samples=5000, seed=42):
    rng = np.random.default_rng(seed)
    years = rng.integers(2000, 2024, size=n_samples)
    mileages = np.round(np.abs(rng.normal(60000, 30000, size=n_samples))).astype(int)
    brands = rng.choice(["Toyota","Honda","Ford","BMW","Audi","Hyundai"], size=n_samples, p=[0.25,0.2,0.2,0.15,0.1,0.1])
    conditions = rng.choice(["Excellent","Good","Fair","Poor"], size=n_samples, p=[0.2,0.5,0.25,0.05])
    engine_sizes = np.round(rng.uniform(1.0, 4.5, size=n_samples),2)
    transmissions = rng.choice(["Automatic","Manual"], size=n_samples, p=[0.85,0.15])

    base_price = 30000
    age = 2024 - years
    price = base_price * (0.9 ** age) - (mileages * 0.05) + engine_sizes * 500
    # brand adjustments
    brand_adj = {"Toyota":1.0,"Honda":1.0,"Ford":0.95,"BMW":1.3,"Audi":1.25,"Hyundai":0.9}
    price = price * np.array([brand_adj[b] for b in brands])
    # condition adjustments
    cond_adj = {"Excellent":1.1,"Good":1.0,"Fair":0.85,"Poor":0.7}
    price = price * np.array([cond_adj[c] for c in conditions])

    # noise and clipping
    price = price + rng.normal(0, 1500, size=n_samples)
    price = np.clip(price, 1000, None)

    df = pd.DataFrame({
        "year": years,
        "mileage": mileages,
        "brand": brands,
        "condition": conditions,
        "engine_size": engine_sizes,
        "transmission": transmissions,
        "price": np.round(price,2)
    })

    return df


def _try_parse_number_series(s: pd.Series) -> pd.Series:
    # try to extract numeric value from strings like '1248 CC' or '18 kmpl'
    def extract(x):
        if pd.isna(x):
            return np.nan
        try:
            if isinstance(x, (int, float, np.number)):
                return x
            x = str(x)
            m = re.search(r"([0-9]+\.?[0-9]*)", x.replace(',', ''))
            if m:
                return float(m.group(1))
        except Exception:
            return np.nan
        return np.nan

    return s.map(extract)


def load_dataset(path: Optional[str] = None) -> Tuple[pd.DataFrame, str]:
    """
    Load dataset from provided path or try to discover `Car_Price_Prediction.csv` in common locations.
    Returns (df, target_col_name).
    If no file is found, returns synthetic data and 'price' as target.
    """
    candidates = []
    if path:
        candidates.append(path)
    # common locations: project root, downloads path used in attachment
    candidates += [
        "Car_Price_Prediction.csv",
        os.path.expanduser(r"~/Downloads/Car_Price_Prediction.csv"),
        os.path.expanduser(r"~/Downloads/archive (1)/Car_Price_Prediction.csv"),
        os.path.join(os.getcwd(), "Car_Price_Prediction.csv"),
        os.path.join(os.getcwd(), "data", "Car_Price_Prediction.csv"),
    ]

    df = None
    for p in candidates:
        try:
            if p and os.path.exists(p):
                df = pd.read_csv(p)
                print(f"Loaded dataset from {p}")
                break
        except Exception:
            continue

    if df is None:
        # fallback to synthetic
        print("No CSV dataset found — falling back to synthetic data generator")
        df = generate_synthetic_car_data(5000)
        return df, "price"

    # find target column by common names
    cols_lower = {c.lower(): c for c in df.columns}
    target_candidates = ["selling_price", "selling price", "sellingprice", "price", "target", "price_usd", "selling_price_inr"]
    target_col = None
    for t in target_candidates:
        if t in cols_lower:
            target_col = cols_lower[t]
            break
    if target_col is None:
        # last resort: numeric column with name containing 'price' or the last numeric column
        for c in df.columns:
            if 'price' in c.lower():
                target_col = c
                break
    if target_col is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            # choose last numeric column as target
            target_col = numeric_cols[-1]

    if target_col is None:
        raise RuntimeError("Could not determine target column in provided CSV. Please provide a dataset with a price/selling_price column.")

    # try to convert object columns that contain numeric text to numeric
    for c in df.select_dtypes(include=[object]).columns:
        parsed = _try_parse_number_series(df[c])
        # if parsed yields many non-nulls, use it
        if parsed.notna().sum() > (0.5 * len(df)):
            df[c] = parsed

    return df, target_col


if __name__ == "__main__":
    df, target = load_dataset()
    print(f"Dataset loaded. Target column: {target}")
    print(df.head())
