# Mortgage Churn Prediction — Streamlit Mock Dashboard

This project is a mock-up Streamlit dashboard for Mortgage Churn Prediction. It provides an executive overview, customer-level predictions, explainability plots (mock SHAP-like visuals), retention recommendations, and exportable reports.

Run locally:

1. Create a Python environment (recommended):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

2. The app will open in your browser at `http://localhost:8501`.

Files:
- `app.py` — Streamlit app with sections described in the spec.
- `data.py` — Generates reproducible mock customer and monthly trend data.
- `utils.py` — Helper functions for CSV/PDF exports and retention suggestions.
- `requirements.txt` — Minimal dependencies.

Notes:
- This is a mock-up for demonstration and exploration. SHAP visuals and recommendations are simulated for the demo.
