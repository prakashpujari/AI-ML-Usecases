# 🚗 Car Price Prediction — Complete ML Pipeline

## Project Overview

A production-grade, end-to-end machine learning pipeline for car price prediction with enterprise-level orchestration, monitoring, and deployment capabilities.

### 🎯 What This Project Does

This project demonstrates a complete ML workflow:
1. **Data Generation & Validation** - Synthetic car data with quality checks
2. **Model Training** - Scikit-learn regression models with hyperparameter tuning
3. **Experiment Tracking** - MLflow integration for versioning and metrics
4. **Workflow Orchestration** - Apache Airflow for automated daily training
5. **API Service** - FastAPI backend for real-time predictions
6. **Interactive Dashboard** - Streamlit UI with model explainability (SHAP)
7. **Database Integration** - PostgreSQL for evaluation metrics storage
8. **Multi-Environment Deployment** - DEV, SIT, UAT, PROD configurations

### 📚 Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **ML Framework** | Scikit-learn | Model training & evaluation |
| **Experiment Tracking** | MLflow | Run versioning, artifact storage |
| **Orchestration** | Apache Airflow | Automated workflow scheduling |
| **API** | FastAPI | High-performance REST API |
| **UI** | Streamlit | Interactive data exploration |
| **Database** | PostgreSQL | Metrics & evaluation results |
| **Containerization** | Docker | Environment consistency |
| **Deployment** | Docker Compose, Kubernetes | Multi-environment support |

# 🚗 Car Price Prediction — Complete ML Pipeline

## 📖 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Quick Start Guide](#quick-start-guide)
5. [Detailed Setup Instructions](#detailed-setup-instructions)
6. [Running Each Component](#running-each-component)
7. [Automatic Retraining System](#automatic-retraining-system) 🔄
8. [API Documentation](#api-documentation)
9. [Using Streamlit Dashboard](#using-streamlit-dashboard)
10. [Airflow Orchestration](#airflow-orchestration)
11. [MLflow Experiment Tracking](#mlflow-experiment-tracking)
12. [Database Operations](#database-operations)
13. [Troubleshooting](#troubleshooting)

---

## Project Overview

A production-grade, end-to-end machine learning pipeline for car price prediction with enterprise-level orchestration, monitoring, and deployment capabilities.

### 🎯 What This Project Does

This project demonstrates a complete ML workflow:
1. **Data Generation & Validation** - Synthetic car data with quality checks
2. **Model Training** - Scikit-learn regression models with hyperparameter tuning
3. **Experiment Tracking** - MLflow integration for versioning and metrics
4. **Workflow Orchestration** - Apache Airflow for automated daily training
5. **API Service** - FastAPI backend for real-time predictions
6. **Interactive Dashboard** - Streamlit UI with model explainability (SHAP)
7. **Database Integration** - PostgreSQL for evaluation metrics storage
8. **🔄 Automatic Retraining** - Drift detection & automatic model retraining on degradation
9. **Model Monitoring** - Performance degradation tracking with automatic alerts
10. **Multi-Environment Deployment** - DEV, SIT, UAT, PROD configurations

### 📚 Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **ML Framework** | Scikit-learn | Model training & evaluation |
| **Experiment Tracking** | MLflow | Run versioning, artifact storage |
| **Orchestration** | Apache Airflow | Automated workflow scheduling |
| **API** | FastAPI | High-performance REST API |
| **UI** | Streamlit | Interactive data exploration |
| **Database** | PostgreSQL | Metrics & evaluation results |
| **Drift Detection** | SciPy, Pandas | Data/concept drift monitoring |
| **Containerization** | Docker | Environment consistency |
| **Deployment** | Docker Compose, Kubernetes | Multi-environment support |

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Streamlit UI          Airflow WebUI        MLflow UI            │
│  (localhost:8501)      (localhost:8080)     (localhost:5000)     │
│                                                                   │
└────────────┬─────────────────────────────────┬──────────────┬────┘
             │                                 │              │
             └─────────────────────────────────┴──────────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
        ┌────▼────┐      ┌────▼────┐     ┌────▼─────┐
        │ FastAPI │      │ Airflow  │     │  MLflow  │
        │  API    │      │ Scheduler│     │ Tracking │
        │(8000)   │      │ (Airflow)│     │ (5000)   │
        └────┬────┘      └────┬────┘     └────┬─────┘
             │                │              │
             └────────────────┼──────────────┘
                              │
                 ┌────────────┼────────────┐
                 │            │            │
            ┌────▼───┐   ┌────▼───┐  ┌────▼────┐
            │  Model │   │  Data  │  │ Metrics │
            │ Storage│   │ Storage│  │Database │
            │(models/│   │(data/) │  │(5433)   │
            │)       │   │        │  └─────────┘
            └────────┘   └────────┘
```

### Data Flow

```
1. DATA GENERATION (train.py)
   ├─ Generate synthetic car data
   └─ Save to data/trainset/train.csv

2. DATA VALIDATION (validate_data task)
   ├─ Check data quality
   ├─ Validate schema
   └─ Log to Airflow

3. MODEL TRAINING (train_model task)
   ├─ Split train/test
   ├─ Train Scikit-learn model
   ├─ Log metrics to MLflow
   └─ Save model to models/trained/

4. MODEL EVALUATION (evaluate_model task)
   ├─ Calculate performance metrics
   ├─ Generate SHAP explanations
   ├─ Store results in PostgreSQL
   └─ Log to MLflow

5. MODEL REGISTRATION (register_model task)
   ├─ Register best model
   ├─ Promote to staging
   └─ Update metrics DB

6. MONITORING & DRIFT DETECTION (automatic_retraining_dag) 🔄
   ├─ Detect data drift (Kolmogorov-Smirnov test)
   ├─ Detect concept drift (error analysis)
   ├─ Check performance degradation (R², RMSE)
   ├─ Calculate severity & confidence
   ├─ Log events to PostgreSQL
   └─ Trigger retraining if needed

7. AUTOMATIC RETRAINING (automatic_retraining_dag) 🔄
   ├─ Prepare training data (merge reference + recent)
   ├─ Execute retraining subprocess
   ├─ Validate improvements
   ├─ Log metrics to database
   └─ Update production model

8. API SERVING (FastAPI)
   ├─ Load model from storage
   ├─ Accept prediction requests
   ├─ Return predictions + confidence
   └─ Log to database

9. UI VISUALIZATION (Streamlit)
   ├─ Display predictions
   ├─ Show SHAP explanations
   ├─ Plot historical metrics
   └─ Interactive feature exploration
```

---

## Prerequisites

### System Requirements

- **OS**: Windows 10/11, macOS, or Linux
- **Python**: 3.9 or higher
- **Docker**: 20.10+ (for containerized setup)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 2GB for dependencies and data

### Software to Install

1. **Python 3.9+** - Download from [python.org](https://www.python.org)
2. **Docker Desktop** - Download from [docker.com](https://www.docker.com)
3. **Git** - Download from [git-scm.com](https://www.git-scm.com)
4. **PostgreSQL (optional for native setup)** - Download from [postgresql.org](https://www.postgresql.org)

### Verify Installation

```powershell
# Check Python
python --version
# Expected: Python 3.9+

# Check Docker
docker --version
# Expected: Docker version 20.10+

# Check Git
git --version
# Expected: git version 2.x
```

---

## Quick Start Guide

### 🚀 Fastest Way to Get Running (Docker - Recommended)

```powershell
# 1. Clone the repository
git clone <repository-url>
cd ml_car_price_predection

# 2. Start all services with Docker Compose
docker-compose -f deployment/dev/docker-compose.dev.yml up -d

# 3. Wait for services to be healthy (30-60 seconds)
docker-compose -f deployment/dev/docker-compose.dev.yml ps

# 4. Access the services
- Streamlit UI:        http://localhost:8501
- FastAPI:             http://localhost:8000
- FastAPI Docs:        http://localhost:8000/docs
- MLflow:              http://localhost:5000
- PostgreSQL:          localhost:5433
```

**Expected Output:**
```
NAME           IMAGE                COMMAND              STATUS
car-api-dev    dev-api              "uvicorn..."         Up 30 seconds
car-ui-dev     dev-ui               "streamlit..."       Up 25 seconds
mlflow-dev     python:3.11-slim     "sh -c..."           Up 60+ seconds
postgres-dev   postgres:15-alpine   "docker-entry..."    Up 60+ seconds (healthy)
```

### 📱 Services URLs After Startup

| Service | URL | Credentials |
|---------|-----|-------------|
| **Streamlit Dashboard** | http://localhost:8501 | None required |
| **FastAPI Docs** | http://localhost:8000/docs | Try it out button |
| **MLflow** | http://localhost:5000 | None required |
| **Database** | postgresql://postgres:postgres@localhost:5433/postgres | psql client |

---

## Detailed Setup Instructions

### Option A: Docker Setup (Recommended for Beginners)

#### Step 1: Clone Repository

```powershell
# On Windows PowerShell
git clone <repository-url>
cd ml_car_price_predection
```

#### Step 2: Verify Docker Installation

```powershell
docker --version
docker ps  # Should show running containers (if any)
```

#### Step 3: Start Development Stack

```powershell
# Start PostgreSQL, MLflow, FastAPI, and Streamlit
docker-compose -f deployment/dev/docker-compose.dev.yml up -d

# Monitor the startup process
docker-compose -f deployment/dev/docker-compose.dev.yml logs -f

# Wait for all services to become healthy (2-3 minutes)
```

**Screenshot Description of Expected Output:**

```
✔ Network dev_ml-network  Created
✔ Container postgres-dev  Started (healthy)
✔ Container mlflow-dev    Started
✔ Container car-api-dev   Started
✔ Container car-ui-dev    Started
```

#### Step 4: Verify All Services Are Running

```powershell
docker-compose -f deployment/dev/docker-compose.dev.yml ps
```

**Expected Output Table:**
```
NAME           IMAGE                 STATUS                PORTS
postgres-dev   postgres:15-alpine    Up 2 minutes (healthy) 0.0.0.0:5433→5432
mlflow-dev     python:3.11-slim      Up 2 minutes          0.0.0.0:5000→5000
car-api-dev    dev-api               Up 2 minutes          0.0.0.0:8000→8000
car-ui-dev     dev-ui                Up 2 minutes          0.0.0.0:8501→8501
```

### Option B: Native Python Setup (For Development)

#### Step 1: Clone and Navigate

```powershell
git clone <repository-url>
cd ml_car_price_predection
```

#### Step 2: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# If you get an execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Step 3: Install Dependencies

```powershell
# Upgrade pip, wheel, setuptools
python -m pip install --upgrade pip wheel setuptools

# Install project dependencies
pip install -r requirements.txt
```

**Expected Output:**
```
Successfully installed numpy-1.24.3 scikit-learn-1.3.0 fastapi-0.100.0 ...
```

#### Step 4: Start Services Individually

**Terminal 1 - FastAPI**:
```powershell
python -m uvicorn predict_api:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete
```

**Terminal 2 - Streamlit**:
```powershell
streamlit run streamlit_app.py
```

**Expected Output:**
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### Option C: Airflow Setup (For Orchestration)

#### Step 1: Verify Astro CLI Installation

```powershell
astro version
```

If not installed:
```powershell
# Install Astronomer CLI
winget install Astronomer.astro
# or download from https://www.astronomer.io/docs/astro/cli/install-cli
```

#### Step 2: Start Airflow

```powershell
astro dev start

# Wait for startup (2-3 minutes)
# You'll see: ✔ Project is running
```

**Expected Output:**
```
✔ Project image has been updated
✔ Project is running
✔ Webserver: http://localhost:8080
✔ Postgres: localhost:5432
✔ Triggered Airflow Config to Restart
```

#### Step 3: Access Airflow UI

```
URL: http://localhost:8080
Username: admin
Password: admin
```

#### Step 4: Trigger Training DAG

In Airflow UI:
1. Navigate to DAGs
2. Find `train_model_dag`
3. Click the Play button (▶️) to trigger
4. Click on the DAG to view execution

---

## Running Each Component

### 1. 🤖 Model Training

#### Option A: Direct Python

```powershell
# Train model with 5000 synthetic samples
python train.py --n-samples 5000

# Train with custom parameters
python train.py --n-samples 10000 --test-size 0.2 --random-state 42
```

**Expected Output:**
```
INFO:root:Generating synthetic car price data...
INFO:root:Created 5000 samples with 11 features
INFO:root:Starting MLflow run...
INFO:root:Training Random Forest model...
INFO:root:Model training completed
INFO:root:R² Score: 0.8765
INFO:root:RMSE: $4,321.45
INFO:root:Model saved to models/trained/model.pkl
```

#### Option B: Via Airflow DAG

```powershell
# Trigger via Airflow CLI
astro dev run dags trigger train_model_dag

# Or via Python API
python -m airflow dags trigger train_model_dag
```

**Airflow UI Screenshot Description:**

The DAG Graph View shows:
```
[validate_data] → [train_model] → [evaluate_model] → [register_model]
                      ↓
                  [Log Metrics]
```

### 2. 🔮 Make Predictions

#### Using FastAPI Directly

```powershell
# Start API server
python -m uvicorn predict_api:app --host 0.0.0.0 --port 8000 --reload
```

#### Using Streamlit UI

1. Open http://localhost:8501
2. Select car features:
   - **Age**: Slider (0-20 years)
   - **Mileage**: Slider (0-200,000 km)
   - **Engine Size**: Slider (1.0-5.0 L)
   - **Brand**: Dropdown selector
3. Click "🔮 Predict Price"
4. View results with confidence interval

**Streamlit UI Screenshot Description:**

```
┌─────────────────────────────────────────┐
│  🚗 Car Price Prediction Dashboard      │
├─────────────────────────────────────────┤
│                                         │
│ 📊 Feature Selection                    │
│ ├─ Age: [====●────] 5 years             │
│ ├─ Mileage: [═══●═════] 75,000 km      │
│ ├─ Engine: [══●══] 2.0L                 │
│ └─ Brand: [Toyota ▼]                    │
│                                         │
│ [🔮 Predict Price Button]               │
│                                         │
├─────────────────────────────────────────┤
│ 💰 PREDICTION RESULT                    │
│                                         │
│ Estimated Price: $18,500                │
│ Confidence: 85% (±$1,200)               │
│                                         │
│ 📈 Feature Importance (SHAP)            │
│ ├─ Mileage: ━━━━━━━━━ (↓ Price)         │
│ ├─ Age: ━━━━━━ (↓ Price)                │
│ └─ Engine: ━━ (↑ Price)                 │
│                                         │
│ 📊 Model Metrics                        │
│ ├─ R² Score: 0.876                      │
│ ├─ RMSE: $4,321                         │
│ └─ Latest Run: 2026-01-05 21:30         │
│                                         │
└─────────────────────────────────────────┘
```

### 3. 📊 MLflow Experiment Tracking

#### Access MLflow UI

```
URL: http://localhost:5000
```

**MLflow UI Screenshot Description:**

```
Experiments List View:
┌─────────────────────────────────────────┐
│ Experiment: car_price_prediction        │
├─────────────────────────────────────────┤
│ Runs:                                   │
│ ├─ Run ID: abc123def456                 │
│ │  ├─ Status: FINISHED                  │
│ │  ├─ Model: Random Forest              │
│ │  ├─ R² Score: 0.876                   │
│ │  ├─ RMSE: 4321.45                     │
│ │  └─ Timestamp: 2026-01-05 21:30:45    │
│ │                                       │
│ └─ Run ID: xyz789uvw012                 │
│    ├─ Status: FINISHED                  │
│    ├─ Model: Gradient Boosting          │
│    ├─ R² Score: 0.891                   │
│    ├─ RMSE: 3987.23                     │
│    └─ Timestamp: 2026-01-05 20:15:30    │
│                                         │
└─────────────────────────────────────────┘
```

#### Compare Model Runs

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Get best run
best_run = client.search_runs(
    experiment_names=["car_price_prediction"],
    filter_string="metrics.r2_score > 0.85",
    order_by=["metrics.r2_score DESC"],
    max_results=1
)[0]

print(f"Best Model R² Score: {best_run.data.metrics['r2_score']}")
print(f"Artifacts: {best_run.data.tags}")
```

---

## API Documentation

### FastAPI Endpoints

#### 1. Health Check

**Request:**
```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-05T21:35:00Z",
  "version": "1.0.0"
}
```

**Code Example:**
```python
import requests

response = requests.get("http://localhost:8000/health")
print(response.json())
# Output: {'status': 'healthy', ...}
```

#### 2. Model Information

**Request:**
```http
GET /info HTTP/1.1
Host: localhost:8000
```

**Response:**
```json
{
  "model_name": "car_price_predictor",
  "model_version": "1.0",
  "input_features": [
    "age", "mileage", "engine_size", 
    "brand", "fuel_type", "transmission",
    "color", "accident_history", "service_history",
    "ownership_history", "current_price"
  ],
  "output": "predicted_price",
  "accuracy_metrics": {
    "r2_score": 0.876,
    "rmse": 4321.45,
    "mae": 3456.78
  }
}
```

#### 3. Make Prediction

**Request:**
```http
POST /predict HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "age": 5,
  "mileage": 75000,
  "engine_size": 2.0,
  "brand": "Toyota",
  "fuel_type": "Petrol",
  "transmission": "Automatic",
  "color": "White",
  "accident_history": false,
  "service_history": true,
  "ownership_history": 1,
  "current_price": 15000
}
```

**Response:**
```json
{
  "predicted_price": 18500.50,
  "confidence_interval": {
    "lower": 17300.25,
    "upper": 19700.75
  },
  "confidence_level": 0.85,
  "feature_importance": {
    "mileage": 0.32,
    "age": 0.28,
    "engine_size": 0.18,
    "brand": 0.15,
    "fuel_type": 0.07
  },
  "model_version": "1.0",
  "timestamp": "2026-01-05T21:35:12Z"
}
```

**Code Examples:**

Python:
```python
import requests

payload = {
    "age": 5,
    "mileage": 75000,
    "engine_size": 2.0,
    "brand": "Toyota",
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "color": "White",
    "accident_history": False,
    "service_history": True,
    "ownership_history": 1,
    "current_price": 15000
}

response = requests.post(
    "http://localhost:8000/predict",
    json=payload
)

result = response.json()
print(f"Predicted Price: ${result['predicted_price']:.2f}")
print(f"Confidence: {result['confidence_level']*100:.1f}%")
```

cURL:
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 5,
    "mileage": 75000,
    "engine_size": 2.0,
    "brand": "Toyota",
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "color": "White",
    "accident_history": false,
    "service_history": true,
    "ownership_history": 1,
    "current_price": 15000
  }'
```

### Interactive API Documentation

**Swagger UI:**
```
http://localhost:8000/docs
```

**Screenshot Description:**

```
┌────────────────────────────────────────────┐
│  Swagger UI - FastAPI Documentation        │
├────────────────────────────────────────────┤
│                                            │
│ GET /health                                │
│ GET /info                                  │
│ POST /predict                              │
│                                            │
│ ┌──────────────────────────────────────┐  │
│ │ POST /predict                        │  │
│ ├──────────────────────────────────────┤  │
│ │                                      │  │
│ │ [Try it out] Button                  │  │
│ │                                      │  │
│ │ Request Body:                        │  │
│ │ {                                    │  │
│ │   "age": 0,                          │  │
│ │   "mileage": 0,                      │  │
│ │   ...                                │  │
│ │ }                                    │  │
│ │                                      │  │
│ │ [Execute] Button                     │  │
│ │                                      │  │
│ │ Response:                            │  │
│ │ {                                    │  │
│ │   "predicted_price": 18500.50,       │  │
│ │   "confidence_interval": {...}       │  │
│ │ }                                    │  │
│ │                                      │  │
│ └──────────────────────────────────────┘  │
│                                            │
└────────────────────────────────────────────┘
```

---

## Automatic Retraining System 🔄

### Overview

The automatic retraining system continuously monitors model performance and data drift, automatically triggering retraining when degradation is detected. This ensures your production model stays accurate without manual intervention.

### Features

#### 1. **Multi-Method Drift Detection**

```python
from scripts.automatic_retraining import AutomaticRetrainingOrchestrator
import pandas as pd

# Load reference and recent data
ref_data = pd.read_csv("data/trainset/train.csv")
recent_data = pd.read_csv("data/recent_data.csv")

# Create orchestrator
orchestrator = AutomaticRetrainingOrchestrator()

# Check if retraining needed
trigger = orchestrator.should_retrain(
    reference_data=ref_data,
    recent_data=recent_data,
    recent_predictions=predictions,
    recent_actuals=actuals,
    current_metrics={'r2': 0.85, 'rmse': 0.35}
)

if trigger.triggered:
    print(f"Retraining needed: {trigger.reason}")
    print(f"Severity: {trigger.severity}")
    print(f"Confidence: {trigger.confidence}%")
```

**Detection Methods:**

| Method | Threshold | Description |
|--------|-----------|-------------|
| **Data Drift** | p < 0.05 | Kolmogorov-Smirnov test detects distribution shift in features |
| **Concept Drift** | > 15% increase | Compares prediction errors across time windows |
| **Performance Drop** | > 5% | Monitors R² score, RMSE, and accuracy |
| **Outliers** | > 5% of data | Z-score based outlier detection (>3σ) |

#### 2. **Severity Classification**

Events are classified by severity to prioritize action:

```
🟢 LOW (< 10%)       → Monitor, log event
🟡 MEDIUM (10-15%)   → Investigate, plan retraining
🟠 HIGH (15-20%)     → Schedule retraining
🔴 CRITICAL (> 20%)  → Immediate retraining
```

#### 3. **Automatic Execution**

The system automatically executes retraining when triggered:

```python
from scripts.retraining_executor import RetrainingExecutor

executor = RetrainingExecutor()
result = executor.execute_full_retraining_pipeline(
    reference_data=ref_data,
    recent_data=recent_data
)

print(f"Retraining Status: {result['status']}")
print(f"New R² Score: {result['new_r2']}")
print(f"Improvement: {result['improvement_r2_percent']}%")
```

#### 4. **Event Logging**

All retraining events are logged to PostgreSQL for audit and analysis:

```sql
-- View recent retraining events
SELECT triggered_at, trigger_type, severity, execution_successful
FROM model_retraining_events
ORDER BY triggered_at DESC
LIMIT 10;

-- Check improvement metrics
SELECT improvement_r2_percent, improvement_rmse_percent, improvement_accuracy_percent
FROM model_retraining_events
WHERE execution_successful = TRUE;
```

### Quick Start

#### 1. **Check if Retraining Needed**

```bash
python scripts/automatic_retraining.py \
  --reference-data data/trainset/train.csv \
  --recent-data data/recent_data.csv \
  --recent-predictions predictions.npy \
  --recent-actuals actuals.npy
```

#### 2. **Execute Retraining Pipeline**

```bash
python scripts/retraining_executor.py \
  --reference-data data/trainset/train.csv \
  --recent-data data/recent_data.csv
```

#### 3. **Schedule with Airflow**

The DAG `automatic_model_retraining` runs every 6 hours:

```bash
# View in Airflow UI
http://localhost:8080/dags/automatic_model_retraining
```

### Configuration

Edit thresholds in `scripts/automatic_retraining.py`:

```python
orchestrator = AutomaticRetrainingOrchestrator(
    data_drift_threshold=0.05,          # KS test p-value threshold
    performance_threshold=0.05,         # R² drop threshold
    min_samples_for_retraining=100,    # Minimum recent samples
    concept_drift_window=100            # Error comparison window
)
```

### Monitoring

Check retraining history and metrics:

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="postgres",
    user="postgres",
    password="postgres"
)

cursor = conn.cursor()

# Get latest event
cursor.execute("""
    SELECT triggered_at, trigger_type, severity, 
           improvement_r2_percent, execution_successful
    FROM model_retraining_events
    ORDER BY triggered_at DESC
    LIMIT 1
""")

event = cursor.fetchone()
print(f"Latest event: {event}")
cursor.close()
conn.close()
```

### Files

- **Detection Logic**: [scripts/automatic_retraining.py](scripts/automatic_retraining.py) (850 lines)
- **Execution**: [scripts/retraining_executor.py](scripts/retraining_executor.py) (600 lines)
- **Airflow DAG**: [airflow/dags/automatic_retraining_dag.py](airflow/dags/automatic_retraining_dag.py)
- **Full Guide**: [AUTOMATIC_RETRAINING_GUIDE.md](AUTOMATIC_RETRAINING_GUIDE.md)
- **Quick Reference**: [AUTOMATIC_RETRAINING_QUICK_REFERENCE.md](AUTOMATIC_RETRAINING_QUICK_REFERENCE.md)

---

## Using Streamlit Dashboard

### Access Dashboard

```
http://localhost:8501
```

### Features

#### 1. Single Prediction
1. Adjust sliders for car features
2. Select brand from dropdown
3. Click "🔮 Predict Price"
4. View prediction with confidence interval

#### 2. Batch Predictions
1. Upload CSV file with car data
2. Click "📤 Process File"
3. Download results as CSV

#### 3. Model Comparison
1. Select two different model runs from dropdown
2. View side-by-side metrics comparison
3. Compare feature importance plots

#### 4. SHAP Explainability
1. Make a prediction
2. Scroll to "🔍 Model Explanation"
3. View SHAP force plot showing feature impacts
4. Red = increases price, Blue = decreases price

#### 5. Historical Performance
1. View "📈 Training History" tab
2. See model metrics over time
3. Track R² Score, RMSE, MAE trends
4. Compare different model versions

**Streamlit Dashboard Screenshot Description:**

```
┌──────────────────────────────────────────┐
│ 🚗 Car Price Prediction Dashboard        │
├──────────────────────────────────────────┤
│                                          │
│ [🔮 Prediction] [📈 Trends] [📊 Metrics]│
│                                          │
│ ────────────────────────────────────────│
│                                          │
│ 📊 FEATURE SELECTION                    │
│                                          │
│ Age (years):                            │
│ [0] ────●────── [20]                   │
│ Current: 5 years                        │
│                                          │
│ Mileage (km):                           │
│ [0] ────●────── [200,000]              │
│ Current: 75,000 km                      │
│                                          │
│ Engine Size (L):                        │
│ [1.0] ──●─── [5.0]                     │
│ Current: 2.0 L                          │
│                                          │
│ Brand:                                  │
│ [Toyota ▼]                              │
│                                          │
│ Fuel Type:                              │
│ [Petrol ▼]                              │
│                                          │
│ [🔮 Predict Price]                      │
│                                          │
│ ────────────────────────────────────────│
│                                          │
│ 💰 PREDICTION RESULT                    │
│                                          │
│ ┌──────────────────────────────────────┐│
│ │ Estimated Price                      ││
│ │                                      ││
│ │           💵 $18,500                 ││
│ │                                      ││
│ │ Confidence Range: $17,300 - $19,700  ││
│ │ Confidence Level: 85% ████░░░░░░     ││
│ │                                      ││
│ └──────────────────────────────────────┘│
│                                          │
│ ────────────────────────────────────────│
│                                          │
│ 🔍 MODEL EXPLANATION (SHAP)             │
│                                          │
│ Feature Impact on Price:                │
│ (Red = increases, Blue = decreases)     │
│                                          │
│ Mileage: ━━━━━━━━━ (↓ $3,200)           │
│ Age: ━━━━━━ (↓ $2,100)                 │
│ Engine: ━━ (↑ $1,500)                  │
│ Brand: ━ (↑ $800)                      │
│                                          │
│ ────────────────────────────────────────│
│                                          │
│ 📈 MODEL METRICS                        │
│                                          │
│ R² Score:  ████████░ 0.876              │
│ RMSE:      $4,321                       │
│ MAE:       $3,457                       │
│ Training Samples: 5,000                 │
│                                          │
│ ────────────────────────────────────────│
│                                          │
│ ✅ Model Performance: Excellent         │
│    (>0.85 R² score)                     │
│                                          │
└──────────────────────────────────────────┘
```

---

## Airflow Orchestration

### Accessing Airflow

```
URL: http://localhost:8080
Username: admin
Password: admin
```

### DAG: train_model_dag

#### DAG Graph

```
                    ┌─────────────┐
                    │  START DATE │
                    │2026-01-01   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ validate_   │
                    │ data        │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   train_    │
                    │   model     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ evaluate_   │
                    │ model       │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  register_  │
                    │  model      │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   monitor_  │
                    │   performance
                    └─────────────┘
```

#### Task Descriptions

| Task | Purpose | Duration | Status |
|------|---------|----------|--------|
| **validate_data** | Check data quality, schema, completeness | ~10s | ✅ |
| **train_model** | Train ML model with hyperparameter tuning | ~2-5m | ✅ |
| **evaluate_model** | Calculate metrics, generate SHAP plots | ~1-2m | ✅ |
| **register_model** | Register in MLflow, update metadata | ~30s | ✅ |
| **monitor_performance** | Log to database, create alerts | ~20s | ✅ |

### Triggering DAG Manually

#### Via Airflow UI

1. Navigate to `http://localhost:8080/home`
2. Find `train_model_dag` in the DAG list
3. Click the ▶️ **Play** button
4. Click on the DAG name to view execution

**Expected Screenshots:**

Graph View:
```
Shows execution progress with green checkmarks
for completed tasks, blue for running, red for failed
```

Log Output:
```
[2026-01-05 21:45:30] INFO - Starting DAG: train_model_dag
[2026-01-05 21:45:31] INFO - Task: validate_data started
[2026-01-05 21:45:35] INFO - Validated 5000 records
[2026-01-05 21:45:36] INFO - Task: validate_data completed ✓
[2026-01-05 21:45:37] INFO - Task: train_model started
...
```

#### Via Command Line

```powershell
# Trigger DAG
astro dev run dags trigger train_model_dag

# View execution logs
astro dev logs --scheduler
```

### Scheduling

The DAG is scheduled to run **daily at 2:00 AM** by default:

```python
default_args = {
    'start_date': datetime(2026, 1, 1),
    'schedule_interval': '0 2 * * *',  # Daily at 2 AM
}
```

To modify schedule, edit [dags/train_dag.py](dags/train_dag.py).

---

## MLflow Experiment Tracking

### Access MLflow

```
http://localhost:5000
```

### Logging Metrics from Code

```python
import mlflow

# Start experiment
mlflow.set_experiment("car_price_prediction")

with mlflow.start_run(run_name="my_model_v1"):
    # Log parameters
    mlflow.log_param("model_type", "Random Forest")
    mlflow.log_param("n_estimators", 100)
    
    # Log metrics
    mlflow.log_metric("r2_score", 0.876)
    mlflow.log_metric("rmse", 4321.45)
    
    # Log model
    mlflow.sklearn.log_model(model, "model")
    
    # Log artifacts
    mlflow.log_artifact("feature_importance.png")

print("Run logged successfully!")
```

### Querying Runs Programmatically

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Get experiment
exp = client.get_experiment_by_name("car_price_prediction")

# List all runs
runs = client.search_runs(experiment_ids=[exp.experiment_id])

for run in runs:
    print(f"Run ID: {run.info.run_id}")
    print(f"R² Score: {run.data.metrics.get('r2_score', 'N/A')}")
    print(f"RMSE: {run.data.metrics.get('rmse', 'N/A')}")
    print("---")
```

---

## Database Operations

### PostgreSQL Connection Details

```
Host: localhost
Port: 5433
Database: postgres
Username: postgres
Password: postgres
```

### Query Results Using Python

```powershell
# List all training runs
python query_results.py runs

# Show metrics for specific run
python query_results.py metrics 1

# Show trend (last 5 runs)
python query_results.py trend 5

# Compare two runs
python query_results.py compare 1 2
```

**Expected Output:**

```
Run ID: 1
├─ Timestamp: 2026-01-05 21:30:45
├─ Model: Random Forest
├─ R² Score: 0.876
├─ RMSE: 4321.45
└─ Status: COMPLETED

Run ID: 2
├─ Timestamp: 2026-01-05 20:15:30
├─ Model: Gradient Boosting
├─ R² Score: 0.891
├─ RMSE: 3987.23
└─ Status: COMPLETED
```

### Direct Database Access

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="postgres",
    user="postgres",
    password="postgres"
)

cursor = conn.cursor()
cursor.execute("""
    SELECT run_id, model_name, r2_score, rmse 
    FROM model_runs 
    ORDER BY created_at DESC 
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"Run: {row[0]}, Model: {row[1]}, R²: {row[2]}, RMSE: {row[3]}")

cursor.close()
conn.close()
```

---

## Troubleshooting

### Issue 1: Services Won't Start

**Problem:**
```
Error: error building, (re)creating or starting project containers
Error response from daemon: Bind for 0.0.0.0:5432 failed: port is already allocated
```

**Solution:**
```powershell
# Check what's using the port
netstat -ano | findstr :5432

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use different port in docker-compose.dev.yml
# Change: "5434:5432" instead of "5433:5432"
```

### Issue 2: FastAPI Connection Refused

**Problem:**
```
ConnectionRefusedError: Failed to establish a new connection
```

**Solution:**
```powershell
# Verify API is running
docker-compose -f deployment/dev/docker-compose.dev.yml ps | findstr api

# If not running, restart it
docker-compose -f deployment/dev/docker-compose.dev.yml restart car-api-dev

# Check logs
docker-compose -f deployment/dev/docker-compose.dev.yml logs car-api-dev
```

### Issue 3: Streamlit Can't Connect to API

**Problem:**
```
streamlit_app.py: Unable to connect to API at http://localhost:8000
```

**Solution:**
1. Ensure API is running on port 8000
2. Modify [streamlit_app.py](streamlit_app.py) line with API URL:
```python
API_URL = "http://host.docker.internal:8000"  # For Docker-based Streamlit
# or
API_URL = "http://localhost:8000"  # For native Streamlit
```

### Issue 4: Database Connection Timeout

**Problem:**
```
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1), port 5433 failed
```

**Solution:**
```powershell
# Ensure PostgreSQL is running and healthy
docker-compose -f deployment/dev/docker-compose.dev.yml ps | findstr postgres-dev

# If unhealthy, restart it
docker-compose -f deployment/dev/docker-compose.dev.yml restart postgres-dev

# Wait 10-15 seconds for health check to pass
Start-Sleep -Seconds 15
docker-compose -f deployment/dev/docker-compose.dev.yml ps
```

### Issue 5: SHAP Installation Fails (Windows)

**Problem:**
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**Solution:**
```powershell
# Install from pre-built wheel
pip install --only-binary :all: shap

# Or use Conda (recommended)
conda install -c conda-forge shap
```

### Issue 6: Airflow DAG Not Appearing

**Problem:**
```
No DAGs appear in Airflow UI
```

**Solution:**
```powershell
# Ensure airflow_settings.yaml is correct
cat airflow_settings.yaml

# Restart Airflow
astro dev stop
astro dev start

# Check DAG parsing
astro dev run dags list
```

---

## Project Structure

```
ml_car_price_predection/
├── src/                           # Main source code
│   ├── data/
│   │   ├── data_generator.py     # Generate synthetic data
│   │   ├── ingestion.py          # Data loading
│   │   ├── preprocessing.py      # Feature engineering
│   │   ├── split_data.py         # Train/test split
│   │   └── validation.py         # Data quality checks
│   ├── models/
│   │   ├── model.py              # Model architecture
│   │   ├── train.py              # Training logic
│   │   ├── evaluate.py           # Evaluation metrics
│   │   └── predict.py            # Inference code
│   └── pipelines/
│       ├── training_pipeline.py  # Full training flow
│       ├── inference_pipeline.py # Prediction pipeline
│       └── monitoring_pipeline.py# Performance monitoring
│
├── dags/                          # Airflow DAGs
│   ├── train_dag.py              # Training orchestration
│   └── automatic_retraining_dag.py # 🔄 Automatic retraining scheduler
│
├── scripts/                       # Utility scripts
│   ├── db_utils.py               # Database utilities
│   ├── data_validation.py        # Data checks
│   ├── monitor.py                # Performance monitoring
│   ├── query_results.py          # Query evaluation metrics
│   ├── automatic_retraining.py   # 🔄 Drift detection engine (850 lines)
│   └── retraining_executor.py    # 🔄 Retraining execution (600 lines)
│
├── models/                        # Model storage
│   ├── trained/                  # Trained model files
│   ├── staging/                  # Staging models
│   └── production/               # Production models
│
├── data/                          # Data storage
│   ├── trainset/                 # Training data
│   └── testset/                  # Test data
│
├── deployment/                    # Environment configs
│   ├── dev/                      # Development setup
│   ├── sit/                      # System integration test
│   ├── uat/                      # User acceptance test
│   └── prod/                     # Production setup
│
├── k8s/                          # Kubernetes manifests
│   ├── deployment-api.yaml
│   ├── deployment-ui.yaml
│   ├── service-api.yaml
│   └── service-ui.yaml
│
├── predict_api.py                # FastAPI app
├── streamlit_app.py              # Streamlit UI
├── train.py                       # Standalone training script
├── requirements.txt              # Python dependencies
├── README.md                      # This file
├── AUTOMATIC_RETRAINING_GUIDE.md # 🔄 Comprehensive retraining guide (2,500+ lines)
└── AUTOMATIC_RETRAINING_QUICK_REFERENCE.md # 🔄 Quick reference & APIs
```

---

## Common Workflows

### Workflow 1: Train New Model and Deploy

```powershell
# 1. Start all services
docker-compose -f deployment/dev/docker-compose.dev.yml up -d

# 2. Train model
python train.py --n-samples 10000

# 3. Check metrics in MLflow
# Visit http://localhost:5000

# 4. Verify API
curl http://localhost:8000/health

# 5. Make prediction in Streamlit
# Visit http://localhost:8501
```

### Workflow 2: Schedule Daily Training

```powershell
# 1. Start Airflow
astro dev start

# 2. Access UI
# http://localhost:8080

# 3. Trigger DAG
# Click play button on train_model_dag

# 4. Monitor execution
# View logs and metrics in real-time
```

### Workflow 3: Compare Model Versions

```python
import mlflow

client = mlflow.tracking.MlflowClient()

# Get experiments
exp = client.get_experiment_by_name("car_price_prediction")

# Get top 2 runs by R² score
runs = client.search_runs(
    experiment_ids=[exp.experiment_id],
    order_by=["metrics.r2_score DESC"],
    max_results=2
)

# Compare
for i, run in enumerate(runs):
    print(f"\nModel {i+1}:")
    print(f"  R² Score: {run.data.metrics['r2_score']:.3f}")
    print(f"  RMSE: {run.data.metrics['rmse']:.2f}")
    print(f"  Created: {run.info.start_time}")
```

---

## Next Steps

1. **Customize with Your Data**: Replace synthetic data with real car listings
2. **Tune Hyperparameters**: Modify [src/models/train.py](src/models/train.py)
3. **Add Features**: Enhance feature engineering in [src/data/preprocessing.py](src/data/preprocessing.py)
4. **Configure Automatic Retraining**: 🔄 Set thresholds in [scripts/automatic_retraining.py](scripts/automatic_retraining.py)
5. **Monitor Drift Events**: Check [AUTOMATIC_RETRAINING_GUIDE.md](AUTOMATIC_RETRAINING_GUIDE.md) for SQL queries
6. **Deploy to Cloud**: Use Kubernetes manifests in [k8s/](k8s/) for Kubernetes deployment
7. **Set Up Alerts**: Monitor model degradation in [scripts/monitor.py](scripts/monitor.py)

---

## What's New in This Version 🔄

### Automatic Model Retraining System

This release introduces **automatic drift detection and model retraining** with:

- **3 Detection Methods**:
  - Data Drift (Kolmogorov-Smirnov test)
  - Concept Drift (error analysis)
  - Performance Degradation (R², RMSE, accuracy)

- **Severity Classification**: LOW, MEDIUM, HIGH, CRITICAL
- **Confidence Scoring**: Each trigger includes confidence metrics
- **Automatic Execution**: Models retrain and update automatically
- **Event Logging**: Full audit trail in PostgreSQL
- **Airflow Integration**: Scheduled every 6 hours with task pipeline

### New Files

- [scripts/automatic_retraining.py](scripts/automatic_retraining.py) - Drift detection engine
- [scripts/retraining_executor.py](scripts/retraining_executor.py) - Execution pipeline
- [airflow/dags/automatic_retraining_dag.py](airflow/dags/automatic_retraining_dag.py) - Airflow scheduling
- [AUTOMATIC_RETRAINING_GUIDE.md](AUTOMATIC_RETRAINING_GUIDE.md) - Comprehensive documentation
- [AUTOMATIC_RETRAINING_QUICK_REFERENCE.md](AUTOMATIC_RETRAINING_QUICK_REFERENCE.md) - Quick reference

---

## Support & Documentation

- **Automatic Retraining**: [AUTOMATIC_RETRAINING_GUIDE.md](AUTOMATIC_RETRAINING_GUIDE.md) 🔄
- **Quick Reference**: [AUTOMATIC_RETRAINING_QUICK_REFERENCE.md](AUTOMATIC_RETRAINING_QUICK_REFERENCE.md) 🔄
- **MLflow Docs**: https://mlflow.org/docs/latest/
- **Airflow Docs**: https://airflow.apache.org/docs/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Streamlit Docs**: https://docs.streamlit.io/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

---

## License

This project is provided as-is for educational and development purposes.

---

**Last Updated**: January 6, 2026  
**Version**: 2.0 (with Automatic Retraining)

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

