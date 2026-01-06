"""
Example integration of model rollback monitoring into Airflow DAG
Demonstrates how to add performance monitoring after model training
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.decorators import apply_defaults
from datetime import datetime, timedelta
import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from db_utils import ModelEvaluationDB
from monitor_model_performance import ModelMonitor


def check_model_performance(**context):
    """
    Check if current production model has degraded and rollback if needed
    Can be added to any DAG after model training
    """
    monitor = ModelMonitor(
        degradation_threshold=5.0,  # 5% threshold
        auto_rollback=True
    )
    
    try:
        result = monitor.check_and_respond()
        
        # Push result to XCom for downstream tasks
        context['task_instance'].xcom_push(
            key='monitoring_result',
            value=result
        )
        
        if result['status'] == 'ROLLED_BACK':
            print(f"⚠️  Model rolled back: {result}")
            # Optionally fail the DAG or send alert
            return 'ROLLBACK_EXECUTED'
        elif result['status'] == 'OK':
            return 'HEALTHY'
        else:
            return 'DEGRADATION_DETECTED'
    
    finally:
        monitor.close()


def compare_model_versions(**context):
    """
    Compare current model with previous version for detailed analysis
    """
    with ModelEvaluationDB() as db:
        history = db.get_model_history(limit=2)
        
        if len(history) >= 2:
            comparison = db.compare_models(
                history[0]['model_version'],
                history[1]['model_version']
            )
            
            print(f"Model Comparison:")
            print(f"  Current: v{comparison['current_version']}")
            print(f"  Previous: v{comparison['previous_version']}")
            print(f"  R² Change: {comparison['r2_change']:.4f}")
            print(f"  Degraded: {comparison['degraded']}")
            
            context['task_instance'].xcom_push(
                key='model_comparison',
                value=comparison
            )
            
            return comparison
        else:
            print("Not enough model versions to compare")
            return None


def handle_degradation(**context):
    """
    Handle model degradation - send alerts, create incidents, etc.
    """
    task_instance = context['task_instance']
    
    # Get results from previous tasks
    monitoring_result = task_instance.xcom_pull(
        task_ids='check_model_performance',
        key='monitoring_result'
    )
    
    if monitoring_result and monitoring_result['status'] == 'ROLLED_BACK':
        print("🚨 Model degradation detected and rollback executed!")
        print(f"Details: {monitoring_result['degradation_check']}")
        
        # Here you could:
        # - Send Slack alert
        # - Create PagerDuty incident
        # - Send email notification
        # - Log to monitoring dashboard
        
        return 'ALERT_SENT'
    else:
        print("✓ Model is healthy - no action needed")
        return 'HEALTHY'


# Default DAG arguments
default_args = {
    'owner': 'ml-team',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email': ['ml-team@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'model_performance_monitoring',
    default_args=default_args,
    description='Monitor model performance and trigger rollbacks',
    schedule_interval='0 * * * *',  # Hourly
    catchup=False,
)

# Task 1: Check model performance
check_performance = PythonOperator(
    task_id='check_model_performance',
    python_callable=check_model_performance,
    dag=dag,
)

# Task 2: Compare model versions
compare_versions = PythonOperator(
    task_id='compare_model_versions',
    python_callable=compare_model_versions,
    dag=dag,
)

# Task 3: Handle any degradation
handle_alert = PythonOperator(
    task_id='handle_degradation_alert',
    python_callable=handle_degradation,
    dag=dag,
)

# Task dependencies
check_performance >> compare_versions >> handle_alert


# ============================================================================
# ALTERNATIVE: Add to existing training DAG
# ============================================================================

"""
If you have an existing training DAG (e.g., train_model_dag.py),
add these lines after the training task:

from airflow.models import DAG
from airflow.operators.python import PythonOperator

# In your existing DAG:
train_task = ...  # Your existing train task

# Add monitoring after training
monitor_task = PythonOperator(
    task_id='monitor_new_model',
    python_callable=check_model_performance,
    dag=dag,
)

# Set dependencies
train_task >> monitor_task
"""


# ============================================================================
# USAGE IN PYTHON CODE (outside Airflow)
# ============================================================================

"""
from scripts.monitor_model_performance import ModelMonitor

# Simple usage:
monitor = ModelMonitor(auto_rollback=True)
result = monitor.check_and_respond()

if result['status'] == 'ROLLED_BACK':
    print(f"Model rolled back!")
    # Send alert to your monitoring system
    send_alert(f"Model degradation detected: {result}")
elif result['status'] == 'OK':
    print("Model is healthy")

monitor.close()
"""
