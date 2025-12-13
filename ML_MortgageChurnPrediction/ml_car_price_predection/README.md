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
uvicorn predict_api:app --host 0.0.0.0 --port 8000 --reload
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

2. Notes:
- The `mlflow` service runs the MLflow UI at `http://localhost:5000` and stores artifacts under `./mlruns`.
- The `train` service runs once and writes `models/model.pkl` to the shared `./models` folder (used by the API and UI).
- The `api` is available at `http://localhost:8000` (FastAPI) and the Streamlit UI at `http://localhost:8501`.

3. To re-run training, you can run only the `train` service:

```powershell
docker-compose run --rm train
```

