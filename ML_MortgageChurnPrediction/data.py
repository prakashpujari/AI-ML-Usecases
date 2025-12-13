import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_data(n_customers: int = 1000, seed: int = 42):
    rng = np.random.default_rng(seed)
    customer_ids = [f"C{rng.integers(10000,99999)}" for _ in range(n_customers)]
    loan_types = rng.choice(["Conventional","VA","FHA"], size=n_customers, p=[0.7,0.15,0.15])
    states = rng.choice(["CA","TX","FL","NY","WA","IL"], size=n_customers)
    branches = [f"BR-{x}" for x in rng.integers(1,50,size=n_customers)]

    # Key features
    apr = np.round(rng.normal(5.5, 1.2, size=n_customers),2)
    balance = np.round(np.abs(rng.normal(250000, 120000, size=n_customers)),2)
    payment_inconsistency = rng.integers(0,6,size=n_customers)
    delinquency_count = rng.integers(0,4,size=n_customers)
    complaints = rng.integers(0,5,size=n_customers)
    online_checks = rng.integers(0,20,size=n_customers)

    # churn probability (synthetic, depends on some features)
    base = 0.05 + 0.000001*balance + 0.05*(payment_inconsistency/5) + 0.12*(delinquency_count)
    base += 0.02*(complaints>1).astype(float)
    base += 0.01*(online_checks>8).astype(float)
    churn_prob = np.clip(rng.normal(base, 0.08), 0, 1)

    df = pd.DataFrame({
        "customer_id": customer_ids,
        "loan_type": loan_types,
        "state": states,
        "branch": branches,
        "apr": apr,
        "balance": balance,
        "payment_inconsistency": payment_inconsistency,
        "delinquency_count": delinquency_count,
        "complaints": complaints,
        "online_checks": online_checks,
        "churn_probability": np.round(churn_prob,3)
    })

    # risk score category
    def risk_label(p):
        if p >= 0.7:
            return "High"
        if p >= 0.4:
            return "Medium"
        return "Low"

    df["risk_level"] = df["churn_probability"].apply(risk_label)

    # Create a monthly trend (last 12 months)
    today = datetime.today().replace(day=1)
    months = [ (today - pd.DateOffset(months=i)).strftime("%Y-%m") for i in range(11,-1,-1) ]
    # generate synthetic monthly churn rates
    rng2 = np.random.default_rng(seed+1)
    trend = pd.DataFrame({
        "month": months,
        "churn_rate": np.round(np.clip(rng2.normal(0.05, 0.01, size=len(months)), 0, 0.2),3)
    })

    return df, trend

if __name__ == "__main__":
    df, trend = generate_mock_data(50)
    print(df.head())
    print(trend)
