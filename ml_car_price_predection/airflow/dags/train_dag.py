"""
Production-Ready Airflow DAG for Car Price Prediction Model Training
Orchestrates daily model training with MLflow tracking, data validation, and model deployment
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta
import os
import logging
import sys

# Add scripts directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

# Configuration
WORKSPACE_DIR = os.getenv('AIRFLOW_WORKSPACE_DIR', '/opt/airflow/dags')
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
MODEL_NAME = 'car_price_predictor'
PRODUCTION_MODEL_PATH = f'{WORKSPACE_DIR}/models/production/model.pkl'

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
    import json
    
    logging.info("Starting data validation...")
    
    # Check if training data exists
    train_data_path = f'{WORKSPACE_DIR}/data/trainset/train.csv'
    if not os.path.exists(train_data_path):
        raise FileNotFoundError(f"Training data not found at {train_data_path}")
    
    df = pd.read_csv(train_data_path)
    
    # Data quality checks
    validation_results = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'missing_values': df.isnull().sum().to_dict(),
        'duplicate_rows': int(df.duplicated().sum()),
        'data_types': df.dtypes.astype(str).to_dict(),
    }
    
    # Check minimum data requirements
    if len(df) < 100:
        raise ValueError(f"Insufficient training data: {len(df)} rows (minimum 100 required)")
    
    # Check for target column
    if 'price' not in df.columns.str.lower():
        raise ValueError("Target column 'price' not found in dataset")
    
    logging.info(f"Data validation passed: {validation_results['total_rows']} rows, {validation_results['total_columns']} columns")
    
    # Push validation results to XCom
    context['ti'].xcom_push(key='validation_results', value=validation_results)
    
    return validation_results

def check_mlflow_server(**context):
    """Verify MLflow server is accessible"""
    import requests
    import time
    
    logging.info(f"Checking MLflow server at {MLFLOW_TRACKING_URI}")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{MLFLOW_TRACKING_URI}/health", timeout=10)
            if response.status_code == 200:
                logging.info("MLflow server is healthy")
                return True
        except Exception as e:
            logging.warning(f"MLflow check attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    
    raise Exception("MLflow server is not accessible")

def train_model(**context):
    """Execute model training with comprehensive MLflow logging"""
    import subprocess
    import sys
    
    logging.info("Starting model training...")
    
    # Set environment variables for training
    env = os.environ.copy()
    env['MLFLOW_TRACKING_URI'] = MLFLOW_TRACKING_URI
    env['PYTHONUNBUFFERED'] = '1'
    
    # Execute training script
    train_script = f'{WORKSPACE_DIR}/train.py'
    
    result = subprocess.run(
        [sys.executable, train_script],
        cwd=WORKSPACE_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=7200  # 2 hour timeout
    )
    
    logging.info(f"Training stdout:\n{result.stdout}")
    
    if result.returncode != 0:
        logging.error(f"Training stderr:\n{result.stderr}")
        raise Exception(f"Training failed with exit code {result.returncode}")
    
    logging.info("Model training completed successfully")
    
    return {'status': 'success', 'message': 'Training completed'}

def evaluate_model(**context):
    """Evaluate trained model and log metrics"""
    import pandas as pd
    import joblib
    import json
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    from db_utils import get_db_connection
    
    logging.info("Starting model evaluation...")
    
    # Load test data
    test_data_path = f'{WORKSPACE_DIR}/data/testset/test.csv'
    if not os.path.exists(test_data_path):
        logging.warning("No separate test data found, skipping additional evaluation")
        return {'status': 'skipped', 'reason': 'No test data'}
    
    # Load model artifacts
    if not os.path.exists(PRODUCTION_MODEL_PATH):
        raise FileNotFoundError(f"Model not found at {PRODUCTION_MODEL_PATH}")
    
    model_artifacts = joblib.load(PRODUCTION_MODEL_PATH)
    model = model_artifacts['model']
    preprocessor = model_artifacts['preprocessor']
    scaler = model_artifacts['scaler']
    metadata = model_artifacts.get('metadata', {})
    
    # Load and prepare test data
    df_test = pd.read_csv(test_data_path)
    target_col = model_artifacts.get('target', 'price')
    
    X_test = df_test.drop(columns=[target_col])
    y_test = df_test[target_col]
    
    # Preprocess and predict
    X_test_processed = preprocessor.transform(X_test)
    X_test_scaled = scaler.transform(X_test_processed)
    predictions = model.predict(X_test_scaled)
    
    # Calculate metrics
    metrics = {
        'mse': float(mean_squared_error(y_test, predictions)),
        'rmse': float(mean_squared_error(y_test, predictions, squared=False)),
        'mae': float(mean_absolute_error(y_test, predictions)),
        'r2_score': float(r2_score(y_test, predictions)),
    }
    
    logging.info(f"Model Evaluation Metrics: {json.dumps(metrics, indent=2)}")
    
    # Save evaluation results
    eval_path = f'{WORKSPACE_DIR}/metrics/evaluation_metrics.json'
    os.makedirs(os.path.dirname(eval_path), exist_ok=True)
    with open(eval_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Store in PostgreSQL database
    try:
        with get_db_connection() as db:
            run_id = metadata.get('mlflow_run_id', 'unknown')
            
            # Insert model run if not exists
            db.insert_model_run(
                run_id=run_id,
                model_name=MODEL_NAME,
                trained_at=datetime.fromisoformat(metadata.get('trained_at', datetime.now().isoformat())),
                metadata=metadata
            )
            
            # Insert evaluation metrics
            db.insert_metrics(run_id, metrics, metric_type='test')
            
            # Store data quality info
            db.insert_data_quality(
                run_id=run_id,
                dataset_type='test',
                total_rows=len(df_test),
                total_columns=len(df_test.columns),
                missing_values=df_test.isnull().sum().to_dict(),
                duplicate_rows=int(df_test.duplicated().sum())
            )
            
            logging.info(f"✓ Evaluation results stored in PostgreSQL database")
            
    except Exception as e:
        logging.error(f"Failed to store results in database: {e}")
        # Continue execution even if DB storage fails
    
    # Push metrics to XCom
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
    
    logging.info(f"Registering model to MLflow Registry: {MODEL_NAME}")
    
    # Get the latest run
    experiment = mlflow.get_experiment_by_name("Default")
    if experiment:
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"],
            max_results=1
        )
        
        if not runs.empty:
            latest_run_id = runs.iloc[0]['run_id']
            model_uri = f"runs:/{latest_run_id}/model"
            
            # Register model
            try:
                model_version = mlflow.register_model(model_uri, MODEL_NAME)
                logging.info(f"Model registered: {MODEL_NAME} version {model_version.version}")
                
                # Get evaluation metrics
                eval_metrics = context['ti'].xcom_pull(task_ids='evaluate_model', key='evaluation_metrics')
                
                # Store in database
                try:
                    with get_db_connection() as db:
                        # Update model run with version info
                        db.insert_model_run(
                            run_id=latest_run_id,
                            model_name=MODEL_NAME,
                            model_version=str(model_version.version),
                            model_stage='None',
                            trained_at=datetime.now()
                        )
                        
                        # Load model artifacts to get hyperparameters
                        model_path = f'{WORKSPACE_DIR}/models/production/model.pkl'
                        if os.path.exists(model_path):
                            artifacts = joblib.load(model_path)
                            metadata = artifacts.get('metadata', {})
                            
                            # Store hyperparameters
                            hyperparams = {
                                'n_estimators': metadata.get('n_estimators', 100),
                                'max_depth': metadata.get('max_depth', 'None'),
                                'sklearn_version': metadata.get('sklearn_version', 'unknown')
                            }
                            db.insert_hyperparameters(latest_run_id, hyperparams)
                        
                        logging.info("✓ Model registration stored in database")
                        
                except Exception as e:
                    logging.error(f"Failed to store in database: {e}")
                
                # Promote to staging if R2 > 0.7
                if eval_metrics and eval_metrics.get('r2_score', 0) > 0.7:
                    client.transition_model_version_stage(
                        name=MODEL_NAME,
                        version=model_version.version,
                        stage="Staging"
                    )
                    logging.info(f"Model promoted to Staging (R2: {eval_metrics['r2_score']:.4f})")
                    
                    # Update stage in database
                    try:
                        with get_db_connection() as db:
                            db.insert_model_run(
                                run_id=latest_run_id,
                                model_name=MODEL_NAME,
                                model_version=str(model_version.version),
                                model_stage='Staging',
                                trained_at=datetime.now()
                            )
                            
                            # Create success alert
                            db.insert_alert(
                                run_id=latest_run_id,
                                alert_type='MODEL_PROMOTED',
                                severity='LOW',
                                message=f'Model v{model_version.version} promoted to Staging with R2={eval_metrics["r2_score"]:.4f}'
                            )
                    except Exception as e:
                        logging.error(f"Failed to update database: {e}")
                
                return {'model_name': MODEL_NAME, 'version': model_version.version}
            except Exception as e:
                logging.warning(f"Model registration failed (may already exist): {e}")
                return {'status': 'failed', 'error': str(e)}
    
    logging.warning("No runs found for model registration")
    return {'status': 'no_runs'}

def cleanup_old_artifacts(**context):
    """Clean up old model artifacts and logs"""
    import shutil
    from datetime import datetime, timedelta
    
    logging.info("Cleaning up old artifacts...")
    
    # Keep artifacts for last 30 days
    cutoff_date = datetime.now() - timedelta(days=30)
    
    # Clean up old model backups
    backup_dir = f'{WORKSPACE_DIR}/models/backups'
    if os.path.exists(backup_dir):
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            if os.path.isfile(item_path):
                mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                if mtime < cutoff_date:
                    os.remove(item_path)
                    logging.info(f"Removed old backup: {item}")
    
    logging.info("Cleanup completed")
    return {'status': 'success'}

def send_training_summary(**context):
    """Generate and log training pipeline summary"""
    import json
    
    # Gather results from all tasks
    validation_results = context['ti'].xcom_pull(task_ids='validate_data', key='validation_results')
    eval_metrics = context['ti'].xcom_pull(task_ids='evaluate_model', key='evaluation_metrics')
    
    summary = {
        'dag_run_id': context['dag_run'].run_id,
        'execution_date': str(context['execution_date']),
        'data_validation': validation_results,
        'model_metrics': eval_metrics,
        'status': 'success'
    }
    
    logging.info("=" * 80)
    logging.info("TRAINING PIPELINE SUMMARY")
    logging.info("=" * 80)
    logging.info(json.dumps(summary, indent=2))
    logging.info("=" * 80)
    
    return summary

# Define the DAG
with DAG(
    'car_price_prediction_training_pipeline',
    default_args=default_args,
    description='Production ML pipeline for car price prediction with daily training',
    schedule='0 2 * * *',  # Daily at 2 AM
    catchup=False,
    max_active_runs=1,
    tags=['ml', 'training', 'car-price', 'production'],
) as dag:
    
    # Task 1: Validate data
    validate_data_task = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
    )
    
    # Task 2: Check MLflow server
    check_mlflow_task = PythonOperator(
        task_id='check_mlflow_server',
        python_callable=check_mlflow_server,
    )
    
    # Task 3: Train model
    train_model_task = PythonOperator(
        task_id='train_model',
        python_callable=train_model,
    )
    
    # Task 4: Evaluate model
    evaluate_model_task = PythonOperator(
        task_id='evaluate_model',
        python_callable=evaluate_model,
    )
    
    # Task 5: Register model to MLflow
    register_model_task = PythonOperator(
        task_id='register_model',
        python_callable=register_model,
    )
    
    # Task 6: Cleanup old artifacts
    cleanup_task = PythonOperator(
        task_id='cleanup_artifacts',
        python_callable=cleanup_old_artifacts,
    )
    
    # Task 7: Send summary
    summary_task = PythonOperator(
        task_id='send_summary',
        python_callable=send_training_summary,
        trigger_rule='all_done',
    )
    
    # Define task dependencies
    [validate_data_task, check_mlflow_task] >> train_model_task
    train_model_task >> evaluate_model_task >> register_model_task
    register_model_task >> cleanup_task >> summary_task
