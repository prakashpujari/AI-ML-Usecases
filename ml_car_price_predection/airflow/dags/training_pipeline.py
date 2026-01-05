"""
Refactored Airflow Training DAG using new modular structure
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import sys

# Add src to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from pipelines.training_pipeline import run_training_pipeline
from data.validation import DataValidator
from data.ingestion import DataIngestion
from utils.logger import setup_logger
from utils.config import DATA_DIR, MLFLOW_TRACKING_URI, MODEL_NAME

logger = setup_logger(__name__)

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


def validate_data_task(**context):
    """Validate training data"""
    logger.info("Starting data validation...")
    
    data_loader = DataIngestion()
    df = data_loader.load_training_data()
    
    validator = DataValidator(min_rows=100, max_missing_percent=30.0)
    result = validator.validate(df)
    
    if not result.is_valid:
        raise ValueError(f"Data validation failed: {result.validation_errors}")
    
    logger.info("Data validation passed!")
    context['ti'].xcom_push(key='validation_result', value=result.__dict__)
    return result.__dict__


def check_mlflow_task(**context):
    """Check MLflow server"""
    import requests
    logger.info(f"Checking MLflow at {MLFLOW_TRACKING_URI}")
    
    try:
        response = requests.get(f"{MLFLOW_TRACKING_URI}/health", timeout=10)
        if response.status_code == 200:
            logger.info("MLflow server is healthy")
            return True
    except Exception as e:
        raise Exception(f"MLflow server not accessible: {e}")


def train_model_task(**context):
    """Execute training pipeline"""
    logger.info("Starting model training...")
    
    results = run_training_pipeline(
        model_type='random_forest',
        n_estimators=100,
        max_depth=None,
        cv_folds=5
    )
    
    context['ti'].xcom_push(key='training_results', value=results)
    logger.info(f"Training complete! Run ID: {results['run_id']}")
    return results


def send_summary_task(**context):
    """Send training summary"""
    validation = context['ti'].xcom_pull(task_ids='validate_data', key='validation_result')
    training = context['ti'].xcom_pull(task_ids='train_model', key='training_results')
    
    summary = {
        'dag_run_id': context['dag_run'].run_id,
        'execution_date': str(context['execution_date']),
        'validation': validation,
        'training': training,
        'status': 'success'
    }
    
    logger.info("="*80)
    logger.info("TRAINING PIPELINE SUMMARY")
    logger.info(f"Run ID: {training.get('run_id')}")
    logger.info(f"R² Score: {training.get('metrics', {}).get('r2_score', 'N/A')}")
    logger.info("="*80)
    
    return summary


with DAG(
    'car_price_training_pipeline_v2',
    default_args=default_args,
    description='Refactored ML training pipeline with modular structure',
    schedule='0 2 * * *',
    catchup=False,
    max_active_runs=1,
    tags=['ml', 'training', 'car-price', 'v2', 'modular'],
) as dag:
    
    validate_data = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data_task,
        provide_context=True,
    )
    
    check_mlflow = PythonOperator(
        task_id='check_mlflow',
        python_callable=check_mlflow_task,
        provide_context=True,
    )
    
    train_model = PythonOperator(
        task_id='train_model',
        python_callable=train_model_task,
        provide_context=True,
    )
    
    send_summary = PythonOperator(
        task_id='send_summary',
        python_callable=send_summary_task,
        provide_context=True,
    )
    
    [validate_data, check_mlflow] >> train_model >> send_summary
