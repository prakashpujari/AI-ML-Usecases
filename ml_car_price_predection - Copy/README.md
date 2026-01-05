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

## 🚀 Environment-Specific Deployment

This project now supports **environment-specific deployments** (DEV, SIT, UAT, PROD) with dedicated configurations:

### Quick Start with Deployment Script:

**Windows PowerShell:**
```powershell
# Development environment
.\deploy.ps1 -Env dev -Action up

# Production environment (requires secrets)
$env:PROD_DB_PASSWORD = "secure_password"
$env:REDIS_PASSWORD = "secure_password"
$env:JWT_SECRET = "secure_secret"
.\deploy.ps1 -Env prod -Action up
```

**Linux/Mac:**
```bash
./deploy.sh dev up
./deploy.sh prod up
```

### Environment Details:

| Environment | Purpose | Key Features | Access |
|-------------|---------|--------------|--------|
| **DEV** | Local development | Hot reload, debug mode | http://localhost:8000 |
| **SIT** | Integration testing | Redis cache, health checks | http://localhost:8001 |
| **UAT** | Pre-production | Nginx proxy, rate limiting | http://localhost/ |
| **PROD** | Production | SSL, monitoring, HA | https://localhost/ |

📚 **See [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) for complete deployment guide**

### Manual Docker Compose:
```powershell
# Development
cd deployment/dev
docker-compose -f docker-compose.dev.yml up --build

# Production
cd deployment/prod
docker-compose -f docker-compose.prod.yml up --build -d
```

## 📊 Production Features

- **MLflow Tracking**: Comprehensive experiment tracking with artifact storage
- **Airflow Orchestration**: Daily training DAG with 7 tasks (validate, train, evaluate, register, monitor)
- **PostgreSQL Integration**: Model evaluation metrics stored in dedicated database
- **Redis Caching**: Response caching for improved performance (SIT/UAT/PROD)
- **Nginx Load Balancing**: Reverse proxy with rate limiting (UAT/PROD)
- **Monitoring Stack**: Prometheus + Grafana for metrics and alerts (PROD)
- **Security**: SSL/TLS, rate limiting, non-root containers, health checks

## 🗄️ Database Integration

Each environment uses a separate PostgreSQL database for storing model evaluation results:

```
DEV:  localhost:5433 → ml_evaluation
SIT:  localhost:5434 → ml_evaluation
UAT:  localhost:5435 → ml_evaluation
PROD: localhost:5436 → ml_evaluation
```

Query evaluation results:
```powershell
python query_results.py runs          # List all model runs
python query_results.py trend 5       # Show trend for last 5 runs
python query_results.py compare 1 2   # Compare two runs
```

📚 **See [docs/DATABASE_INTEGRATION.md](docs/DATABASE_INTEGRATION.md) for database schema**

## ☁️ Airflow & Orchestration

The production training pipeline runs daily via Airflow with comprehensive monitoring:

```bash
# Start Airflow (Astronomer)
astro dev start

# Access Airflow UI
http://localhost:8080

# Trigger training DAG manually
python -m airflow dags trigger train_model_dag
```

**DAG Tasks:**
1. Data validation
2. MLflow server health check
3. Model training
4. Model evaluation
5. Model registration
6. Artifact cleanup
7. Summary report

📚 **See [airflow/dags/train_dag.py](airflow/dags/train_dag.py) for DAG configuration**

## 🧪 Kubernetes Deployment

- Build API image: `docker build -t <your-registry>/carprice-api:latest -f deployment/prod/Dockerfile.api .`
- Build UI image: `docker build -t <your-registry>/carprice-ui:latest -f deployment/prod/Dockerfile.ui .`
- Apply k8s manifests: `kubectl apply -f k8s/`

📚 **See [k8s/](k8s/) for Kubernetes manifests**

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

