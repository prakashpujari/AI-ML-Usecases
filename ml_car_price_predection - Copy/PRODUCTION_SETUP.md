# Production ML Pipeline - Setup Guide

## 🚀 Quick Start

This is a production-ready car price prediction ML pipeline with Airflow orchestration and MLflow tracking.

### Start Services

```bash
# Start MLflow
docker-compose up mlflow -d

# Start Airflow (wait for initialization)
astro dev start --wait 5m

# Access services:
# - Airflow UI: http://localhost:8080 (admin/admin)
# - MLflow UI: http://localhost:5000
```

### Trigger Training Pipeline

**Option 1: Airflow UI**
1. Go to http://localhost:8080
2. Find DAG: `car_price_prediction_training_pipeline`
3. Click "Play" button to trigger

**Option 2: Command Line**
```bash
astro dev run dags trigger car_price_prediction_training_pipeline
```

## 📊 Pipeline Features

### Daily Automated Training
- **Schedule**: Every day at 2 AM
- **Tasks**: Data validation → Training → Evaluation → Model Registry → Cleanup
- **Monitoring**: Comprehensive metrics and alerts

### MLflow Integration
- Experiment tracking with all hyperparameters
- Model registry with automatic versioning
- Feature importance and model signatures
- Artifact storage (models, metrics, plots)

### Production Components
1. **Data Validation** (`scripts/data_validation.py`)
2. **Model Training** (`train.py`) with comprehensive logging
3. **Model Registry** (`scripts/model_registry.py`) with auto-promotion
4. **Monitoring** (`scripts/monitor.py`) with drift detection

## 📁 Key Files

- `airflow/dags/train_dag.py` - Production training pipeline
- `train.py` - Enhanced training script with MLflow
- `scripts/data_validation.py` - Data quality checks
- `scripts/model_registry.py` - Model lifecycle management
- `scripts/monitor.py` - Performance monitoring

## 🔧 Configuration

See `deployment/README.md` for full documentation.
