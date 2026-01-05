"""
Production-Ready Airflow DAG for Car Price Prediction Model Training
Placed in top-level `dags/` so Astronomer/Airflow can discover it.
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import sys
import logging

# Resolve repository root and scripts path relative to this file
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DIR = os.path.join(ROOT_DIR, 'scripts')
sys.path.insert(0, SCRIPTS_DIR)

WORKSPACE_DIR = os.getenv('AIRFLOW_WORKSPACE_DIR', ROOT_DIR)
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
MODEL_NAME = 'car_price_predictor'
PRODUCTION_MODEL_PATH = os.path.join(WORKSPACE_DIR, 'models', 'production', 'model.pkl')

# Default args
default_args = {
    'owner': 'ml-team',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email': ['mailtopprakash01@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}


def validate_data(**context):
    """Validate training data quality and completeness"""
    import pandas as pd

    logging.info("Starting data validation...")
    train_data_path = os.path.join(WORKSPACE_DIR, 'data', 'trainset', 'train.csv')
    if not os.path.exists(train_data_path):
        raise FileNotFoundError(f"Training data not found at {train_data_path}")

    df = pd.read_csv(train_data_path)
    validation_results = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'missing_values': df.isnull().sum().to_dict(),
        'duplicate_rows': int(df.duplicated().sum()),
        'data_types': df.dtypes.astype(str).to_dict(),
    }

    if len(df) < 100:
        raise ValueError(f"Insufficient training data: {len(df)} rows (minimum 100 required)")
    if 'price' not in df.columns.str.lower():
        raise ValueError("Target column 'price' not found in dataset")

    context['ti'].xcom_push(key='validation_results', value=validation_results)
    logging.info("Data validation passed")
    return validation_results


def check_mlflow_server(**context):
    """Verify MLflow server is accessible"""
    import requests, time
    logging.info(f"Checking MLflow server at {MLFLOW_TRACKING_URI}")
    for attempt in range(3):
        try:
            resp = requests.get(f"{MLFLOW_TRACKING_URI}/health", timeout=10)
            if resp.status_code == 200:
                return True
        except Exception as exc:
            logging.warning(f"MLflow check attempt {attempt+1}/3 failed: {exc}")
            if attempt < 2:
                time.sleep(5)
    raise Exception("MLflow server is not accessible")


def train_model(**context):
    """Execute model training with comprehensive MLflow logging"""
    import subprocess
    env = os.environ.copy()
    env['MLFLOW_TRACKING_URI'] = MLFLOW_TRACKING_URI
    env['PYTHONUNBUFFERED'] = '1'
    train_script = os.path.join(WORKSPACE_DIR, 'train.py')

    result = subprocess.run(
        [sys.executable, train_script],
        cwd=WORKSPACE_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=7200,
    )
    logging.info(f"Training stdout:\n{result.stdout}")
    if result.returncode != 0:
        logging.error(f"Training stderr:\n{result.stderr}")
        raise Exception(f"Training failed with exit code {result.returncode}")
    return {'status': 'success', 'message': 'Training completed'}


def evaluate_model(**context):
    """Evaluate trained model and log metrics"""
    import pandas as pd
    import joblib
    import json
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    from db_utils import get_db_connection

    test_data_path = os.path.join(WORKSPACE_DIR, 'data', 'testset', 'test.csv')
    if not os.path.exists(test_data_path):
        logging.warning("No separate test data found, skipping evaluation")
        return {'status': 'skipped', 'reason': 'No test data'}

    if not os.path.exists(PRODUCTION_MODEL_PATH):
        raise FileNotFoundError(f"Model not found at {PRODUCTION_MODEL_PATH}")

    artifacts = joblib.load(PRODUCTION_MODEL_PATH)
    model = artifacts['model']
    preprocessor = artifacts['preprocessor']
    scaler = artifacts['scaler']
    metadata = artifacts.get('metadata', {})
    target_col = artifacts.get('target', 'price')

    df_test = pd.read_csv(test_data_path)
    X_test = df_test.drop(columns=[target_col])
    y_test = df_test[target_col]
    X_proc = preprocessor.transform(X_test)
    X_scaled = scaler.transform(X_proc)
    preds = model.predict(X_scaled)

    metrics = {
        'mse': float(mean_squared_error(y_test, preds)),
        'rmse': float(mean_squared_error(y_test, preds, squared=False)),
        'mae': float(mean_absolute_error(y_test, preds)),
        'r2_score': float(r2_score(y_test, preds)),
    }

    os.makedirs(os.path.join(WORKSPACE_DIR, 'metrics'), exist_ok=True)
    with open(os.path.join(WORKSPACE_DIR, 'metrics', 'evaluation_metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=2)

    try:
        with get_db_connection() as db:
            run_id = metadata.get('mlflow_run_id', 'unknown')
            db.insert_model_run(
                run_id=run_id,
                model_name=MODEL_NAME,
                trained_at=datetime.fromisoformat(metadata.get('trained_at', datetime.now().isoformat())),
                metadata=metadata,
            )
            db.insert_metrics(run_id, metrics, metric_type='test')
            db.insert_data_quality(
                run_id=run_id,
                dataset_type='test',
                total_rows=len(df_test),
                total_columns=len(df_test.columns),
                missing_values=df_test.isnull().sum().to_dict(),
                duplicate_rows=int(df_test.duplicated().sum()),
            )
    except Exception as exc:
        logging.error(f"Failed to store results in DB: {exc}")
    context['ti'].xcom_push(key='evaluation_metrics', value=metrics)
    return metrics


def register_model(**context):
    """Register model to MLflow Model Registry"""
    import mlflow
    from mlflow.tracking import MlflowClient
    from db_utils import get_db_connection
    import joblib

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()
    experiment = mlflow.get_experiment_by_name("Default")
    if not experiment:
        logging.warning("No MLflow experiment found")
        return {'status': 'no_runs'}

    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["start_time DESC"],
        max_results=1,
    )
    if runs.empty:
        logging.warning("No runs found for model registration")
        return {'status': 'no_runs'}

    latest_run_id = runs.iloc[0]['run_id']
    model_uri = f"runs:/{latest_run_id}/model"

    try:
        model_version = mlflow.register_model(model_uri, MODEL_NAME)
        eval_metrics = context['ti'].xcom_pull(task_ids='evaluate_model', key='evaluation_metrics')
        try:
            with get_db_connection() as db:
                db.insert_model_run(
                    run_id=latest_run_id,
                    model_name=MODEL_NAME,
                    model_version=str(model_version.version),
                    model_stage='None',
                    trained_at=datetime.now(),
                )
                model_path = PRODUCTION_MODEL_PATH
                if os.path.exists(model_path):
                    artifacts = joblib.load(model_path)
                    metadata = artifacts.get('metadata', {})
                    hyperparams = {
                        'n_estimators': metadata.get('n_estimators', 100),
                        'max_depth': metadata.get('max_depth', 'None'),
                        'sklearn_version': metadata.get('sklearn_version', 'unknown'),
                    }
                    db.insert_hyperparameters(latest_run_id, hyperparams)
        except Exception as exc:
            logging.error(f"Failed to store registration in DB: {exc}")

        if eval_metrics and eval_metrics.get('r2_score', 0) > 0.7:
            client.transition_model_version_stage(
                name=MODEL_NAME,
                version=model_version.version,
                stage="Staging",
            )
        return {'model_name': MODEL_NAME, 'version': model_version.version}
    except Exception as exc:
        logging.warning(f"Model registration failed: {exc}")
        return {'status': 'failed', 'error': str(exc)}


def cleanup_old_artifacts(**context):
    """Clean up old model artifacts and logs"""
    import shutil
    cutoff = datetime.now() - timedelta(days=30)
    backup_dir = os.path.join(WORKSPACE_DIR, 'models', 'backups')
    if os.path.exists(backup_dir):
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            if os.path.isfile(item_path):
                mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                if mtime < cutoff:
                    os.remove(item_path)
    return {'status': 'success'}


def send_training_summary(**context):
    """Generate and log training pipeline summary"""
    import json
    validation_results = context['ti'].xcom_pull(task_ids='validate_data', key='validation_results')
    eval_metrics = context['ti'].xcom_pull(task_ids='evaluate_model', key='evaluation_metrics')
    summary = {
        'dag_run_id': context['dag_run'].run_id,
        'execution_date': str(context['execution_date']),
        'data_validation': validation_results,
        'model_metrics': eval_metrics,
        'status': 'success',
    }
    logging.info(json.dumps(summary, indent=2))
    return summary


with DAG(
    'car_price_prediction_training_pipeline',
    default_args=default_args,
    description='Production ML pipeline for car price prediction with daily training',
    schedule_interval='0 2 * * *',
    catchup=False,
    max_active_runs=1,
    tags=['ml', 'training', 'car-price', 'production'],
) as dag:

    validate_data_task = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
        provide_context=True,
    )

    check_mlflow_task = PythonOperator(
        task_id='check_mlflow_server',
        python_callable=check_mlflow_server,
        provide_context=True,
    )

    train_model_task = PythonOperator(
        task_id='train_model',
        python_callable=train_model,
        provide_context=True,
    )

    evaluate_model_task = PythonOperator(
        task_id='evaluate_model',
        python_callable=evaluate_model,
        provide_context=True,
    )

    register_model_task = PythonOperator(
        task_id='register_model',
        python_callable=register_model,
        provide_context=True,
    )

    cleanup_task = PythonOperator(
        task_id='cleanup_artifacts',
        python_callable=cleanup_old_artifacts,
        provide_context=True,
    )

    summary_task = PythonOperator(
        task_id='send_summary',
        python_callable=send_training_summary,
        provide_context=True,
        trigger_rule='all_done',
    )

    [validate_data_task, check_mlflow_task] >> train_model_task
    train_model_task >> evaluate_model_task >> register_model_task
    register_model_task >> cleanup_task >> summary_task
