# Car Price Prediction — End-to-End (MLflow, Airflow, FastAPI, Streamlit, Docker, Kubernetes)

This folder contains a minimal, production-minded scaffold for an end-to-end car price prediction service. It includes:

- Synthetic data generator and training script with MLflow tracking.
- A FastAPI prediction service with a Dockerfile.
- A Streamlit app for exploration and model explainability (SHAP).
- An example Airflow DAG to orchestrate training.
- Kubernetes manifests for deploying the API and Streamlit app.

This is a scaffold intended to be adapted for real data and cloud infra.

Quick local steps
1. Create and activate venv, install dependencies:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run training (logs to local MLflow run folder):

```powershell
python train.py --n-samples 5000
```

3. Start the API (development):

```powershell
python -m uvicorn predict_api:app --host 0.0.0.0 --port 8000 --reload
```

4. Start the Streamlit UI:

```powershell
streamlit run streamlit_app.py
```

Docker & Kubernetes
- Build API image: `docker build -t <your-registry>/carprice-api:latest -f Dockerfile.api .`
- Build Streamlit image: `docker build -t <your-registry>/carprice-ui:latest -f Dockerfile.ui .`
- Apply k8s manifests in `k8s/` (update image paths): `kubectl apply -f k8s/`

Airflow
- The `airflow/dags/train_dag.py` shows a simple DAG (PythonOperator) that runs the training script. To run it, set up an Airflow instance and place DAG file in `dags/`.

Notes
- Replace synthetic data with your dataset and adjust feature engineering and model selection accordingly.
- For production MLflow, use a proper backend store (e.g., Postgres) and artifact store (S3).

Docker Compose (quick demo)
1. From the `ml_car_price_predection` directory, build and bring up services:

```powershell
docker-compose up --build mlflow train api ui
```

---

## Changes & Fixes Applied (Dec 16, 2025)

This repository was updated to resolve runtime errors and improve developer UX. Key changes:

- `predict_api.py`: cleaned duplicated/embedded code, added proper imports (`Optional`) and restored a single, working FastAPI app with `/health`, `/info`, and `/predict` endpoints. This fixes NameError and import-related crashes when starting the API.
- `streamlit_app.py`: added a safe import for `shap` (wrapped in try/except) and a runtime `HAS_SHAP` check so the Streamlit UI shows a helpful message instead of crashing when `shap` is missing. Also corrected SHAP-block indentation and error handling.
- `requirements.txt`: includes `shap>=0.42` (note: `shap` may require build tools on Windows; see Troubleshooting below).

## How to run locally (recommended quick flow)

1. Create and activate virtual environment (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install Python dependencies:

```powershell
python -m pip install --upgrade pip wheel setuptools
python -m pip install -r requirements.txt
```

If `pip install -r requirements.txt` fails with errors related to `shap` or other packages on Windows, see Troubleshooting.

3. Run the API (development):

```powershell
python -m uvicorn predict_api:app --host 0.0.0.0 --port 8000 --reload
```

4. In another shell, run the Streamlit UI:

```powershell
streamlit run streamlit_app.py
```

Visit `http://localhost:8501` for the UI and `http://localhost:8000/docs` for FastAPI docs.

## Troubleshooting

- Connection refused when Streamlit calls API (e.g., "Failed to establish a new connection"):
	- Ensure the API is running (`uvicorn` logs should show "Uvicorn running on http://0.0.0.0:8000").
	- If you started the API inside Docker Compose, ensure the `api` service is healthy and `docker-compose ps` shows it listening on `0.0.0.0:8000`.
	- Check `predict_api.py` import/runtime errors by running the API in the foreground (`python -m uvicorn ...`) and watching logs.

- `pip install -r requirements.txt` fails (common on Windows with `shap`):
	- Upgrade pip, wheel, setuptools first: `python -m pip install --upgrade pip wheel setuptools`
	- Install a prebuilt wheel for `shap` if available, or install from conda: `conda install -c conda-forge shap`
	- As a temporary workaround, remove/comment `shap` from `requirements.txt`, install the rest, then install `shap` separately via conda or a compatible wheel.

- If model loading fails: make sure `models/model.pkl` exists (training step writes this file). Run `python train.py --n-samples 5000` to produce it.

## Optional: run with Docker Compose

```powershell
docker-compose up --build api ui
```

Use `docker-compose logs -f api` to inspect API startup logs.

---

If you'd like, I can:

- add a Streamlit fallback to call the local `models/model.pkl` directly when the API is down (so the UI still predicts without the API),
- add `shap` to the model artifact `mlruns/.../artifacts/requirements.txt`, or
- attempt to reproduce and fix the `pip install` failure observed in your environment (paste the pip error output here and I'll diagnose).


2. Notes:
- The `mlflow` service runs the MLflow UI at `http://localhost:5000` and stores artifacts under `./mlruns`.
- The `train` service runs once and writes `models/model.pkl` to the shared `./models` folder (used by the API and UI).
- The `api` is available at `http://localhost:8000` (FastAPI) and the Streamlit UI at `http://localhost:8501`.

3. To re-run training, you can run only the `train` service:

```powershell
docker-compose run --rm train
```

