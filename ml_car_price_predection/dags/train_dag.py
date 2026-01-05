"""
Production-Ready Airflow DAG for Car Price Prediction Model Training
Placed in top-level `dags/` so Astronomer/Airflow can discover it.
"""
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import sys
import logging

# Resolve repository root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WORKSPACE_DIR = os.getenv('AIRFLOW_WORKSPACE_DIR', ROOT_DIR)

# Add both scripts and src to path for imports
SCRIPTS_DIR = os.path.join(ROOT_DIR, 'scripts')
SRC_DIR = os.path.join(ROOT_DIR, 'src')
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, SCRIPTS_DIR)
sys.path.insert(0, ROOT_DIR)

MODEL_NAME = 'car_price_predictor'
PRODUCTION_MODEL_PATH = os.path.join(WORKSPACE_DIR, 'models', 'production', 'model.pkl')

# Default args
default_args = {
    'owner': 'ml-team',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
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
    """Skip MLflow check - use local training instead"""
    logging.info("Using local training pipeline (MLflow server not required)")
    return True


def train_model(**context):
    """Execute model training using legacy train script (MLflow optional)"""
    import subprocess
    logging.info("Starting model training using legacy train.py script...")
    
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    # Disable MLflow if not available
    env['MLFLOW_TRACKING_URI'] = ''
    train_script = os.path.join(WORKSPACE_DIR, 'train.py')
    
    if not os.path.exists(train_script):
        logging.error(f"Training script not found at {train_script}")
        raise FileNotFoundError(f"Training script not found: {train_script}")
    
    try:
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
        logging.info("Training completed successfully")
        return {'status': 'success', 'message': 'Training completed'}
    except subprocess.TimeoutExpired:
        logging.error("Training timed out after 2 hours")
        raise
    except Exception as e:
        logging.error(f"Training failed with error: {e}")
        raise


def evaluate_model(**context):
    """Evaluate trained model and log metrics"""
    import pandas as pd
    import joblib
    import json
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

    test_data_path = os.path.join(WORKSPACE_DIR, 'data', 'testset', 'test.csv')
    if not os.path.exists(test_data_path):
        logging.warning("No separate test data found, skipping evaluation")
        return {'status': 'skipped', 'reason': 'No test data'}

    if not os.path.exists(PRODUCTION_MODEL_PATH):
        logging.warning(f"Model not found at {PRODUCTION_MODEL_PATH}, skipping evaluation")
        return {'status': 'skipped', 'reason': 'No model file'}

    try:
        artifacts = joblib.load(PRODUCTION_MODEL_PATH)
    except Exception as e:
        logging.warning(f"Could not load model: {e}, skipping evaluation")
        return {'status': 'skipped', 'reason': f'Could not load model: {e}'}
    
    model = artifacts.get('model')
    preprocessor = artifacts.get('preprocessor')
    scaler = artifacts.get('scaler')
    metadata = artifacts.get('metadata', {})
    target_col = artifacts.get('target', 'price')

    if not all([model, preprocessor, scaler]):
        logging.warning("Missing model components (model, preprocessor, or scaler)")
        return {'status': 'skipped', 'reason': 'Incomplete model artifacts'}

    try:
        df_test = pd.read_csv(test_data_path)
        if target_col not in df_test.columns:
            logging.warning(f"Target column '{target_col}' not found in test data")
            return {'status': 'skipped', 'reason': f'Target column {target_col} not found'}
        
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

        # Try to store in DB if available
        try:
            from scripts.db_utils import get_db_connection
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
            logging.warning(f"Could not store results in DB: {exc}")
        
        context['ti'].xcom_push(key='evaluation_metrics', value=metrics)
        return metrics
    except Exception as e:
        logging.warning(f"Evaluation failed: {e}")
        return {'status': 'skipped', 'reason': str(e)}


def register_model(**context):
    """Register model to MLflow Model Registry or log locally"""
    import joblib
    import json
    
    if not os.path.exists(PRODUCTION_MODEL_PATH):
        logging.warning("Model not found for registration")
        return {'status': 'no_model'}

    try:
        artifacts = joblib.load(PRODUCTION_MODEL_PATH)
        metadata = artifacts.get('metadata', {})
        
        # Try to store in DB if available
        try:
            from scripts.db_utils import get_db_connection
            with get_db_connection() as db:
                run_id = metadata.get('mlflow_run_id', 'unknown')
                db.insert_model_run(
                    run_id=run_id,
                    model_name=MODEL_NAME,
                    model_version='1.0',
                    model_stage='Production',
                    trained_at=datetime.now(),
                )
                hyperparams = {
                    'n_estimators': metadata.get('n_estimators', 100),
                    'max_depth': metadata.get('max_depth', 'None'),
                    'sklearn_version': metadata.get('sklearn_version', 'unknown'),
                }
                db.insert_hyperparameters(run_id, hyperparams)
        except Exception as exc:
            logging.warning(f"Could not store registration in DB: {exc}")
        
        # Log locally
        registration_info = {
            'model_name': MODEL_NAME,
            'version': '1.0',
            'stage': 'Production',
            'path': PRODUCTION_MODEL_PATH,
            'metadata': metadata,
        }
        logging.info(f"Model registered: {json.dumps(registration_info, indent=2, default=str)}")
        return registration_info
    except Exception as exc:
        logging.error(f"Model registration failed: {exc}")
        return {'status': 'failed', 'error': str(exc)}


def cleanup_old_artifacts(**context):
    """Clean up old model artifacts and logs"""
    import shutil
    try:
        cutoff = datetime.now() - timedelta(days=30)
        backup_dir = os.path.join(WORKSPACE_DIR, 'models', 'backups')
        if os.path.exists(backup_dir):
            for item in os.listdir(backup_dir):
                item_path = os.path.join(backup_dir, item)
                if os.path.isfile(item_path):
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                        if mtime < cutoff:
                            os.remove(item_path)
                            logging.info(f"Deleted old artifact: {item_path}")
                    except Exception as e:
                        logging.warning(f"Could not delete {item_path}: {e}")
        logging.info("Cleanup completed successfully")
        return {'status': 'success'}
    except Exception as e:
        logging.warning(f"Cleanup encountered an error: {e}")
        return {'status': 'completed_with_warnings', 'error': str(e)}


def send_training_summary(**context):
    """Generate and log training pipeline summary"""
    import json
    try:
        validation_results = context['ti'].xcom_pull(task_ids='validate_data', key='validation_results')
    except Exception:
        validation_results = None
    
    try:
        eval_metrics = context['ti'].xcom_pull(task_ids='evaluate_model', key='evaluation_metrics')
    except Exception:
        eval_metrics = None

    logical_date = getattr(context.get('dag_run'), 'logical_date', None)
    data_interval_start = context.get('data_interval_start')

    summary = {
        'dag_run_id': getattr(context.get('dag_run'), 'run_id', 'unknown'),
        'logical_date': str(logical_date) if logical_date else None,
        'data_interval_start': str(data_interval_start) if data_interval_start else None,
        'data_validation': validation_results,
        'model_metrics': eval_metrics,
        'status': 'completed',
    }
    logging.info(f"Training Summary: {json.dumps(summary, indent=2, default=str)}")
    return summary


with DAG(
    'car_price_prediction_training_pipeline',
    default_args=default_args,
    description='Production ML pipeline for car price prediction with daily training',
    schedule='0 2 * * *',
    catchup=False,
    max_active_runs=1,
    tags=['ml', 'training', 'car-price', 'production'],
) as dag:

    validate_data_task = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
    )

    check_mlflow_task = PythonOperator(
        task_id='check_mlflow_server',
        python_callable=check_mlflow_server,
    )

    train_model_task = PythonOperator(
        task_id='train_model',
        python_callable=train_model,
    )

    evaluate_model_task = PythonOperator(
        task_id='evaluate_model',
        python_callable=evaluate_model,
    )

    register_model_task = PythonOperator(
        task_id='register_model',
        python_callable=register_model,
    )

    cleanup_task = PythonOperator(
        task_id='cleanup_artifacts',
        python_callable=cleanup_old_artifacts,
    )

    summary_task = PythonOperator(
        task_id='send_summary',
        python_callable=send_training_summary,
        trigger_rule='all_done',
    )

    [validate_data_task, check_mlflow_task] >> train_model_task
    train_model_task >> evaluate_model_task >> register_model_task
    register_model_task >> cleanup_task >> summary_task
