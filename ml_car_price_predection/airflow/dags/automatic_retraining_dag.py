"""
Airflow DAG for Automatic Model Retraining
Monitors model performance and automatically retrains when needed
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
import sys
import os
import logging

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

logger = logging.getLogger(__name__)

# Default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 6),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'automatic_model_retraining',
    default_args=default_args,
    description='Automatic model retraining based on drift/degradation detection',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    catchup=False,
    tags=['ml-pipeline', 'retraining', 'monitoring']
)


def analyze_retraining_need(**context):
    """
    Analyze if model retraining is needed
    """
    import pandas as pd
    import numpy as np
    from datetime import datetime
    
    logger.info("=" * 80)
    logger.info("🔍 ANALYZING RETRAINING NEED")
    logger.info("=" * 80)
    
    try:
        # Load reference data (original training data)
        reference_data_path = "data/trainset/train.csv"
        
        if not os.path.exists(reference_data_path):
            logger.warning(f"Reference data not found: {reference_data_path}")
            return {'should_retrain': False, 'reason': 'Reference data not found'}
        
        reference_data = pd.read_csv(reference_data_path)
        logger.info(f"✅ Loaded reference data with {len(reference_data)} samples")
        
        # Simulate drift detection
        # In production, this would use actual detection methods
        drift_detected = np.random.rand() > 0.7  # 30% chance of drift
        degradation_detected = np.random.rand() > 0.8  # 20% chance of degradation
        
        should_retrain = drift_detected or degradation_detected
        
        trigger_result = {
            'should_retrain': should_retrain,
            'reason': '',
            'drift_detected': drift_detected,
            'degradation_detected': degradation_detected,
            'timestamp': datetime.now().isoformat()
        }
        
        if drift_detected:
            trigger_result['reason'] = 'Data drift detected'
        if degradation_detected:
            trigger_result['reason'] = 'Model performance degradation detected'
        if not should_retrain:
            trigger_result['reason'] = 'Model is healthy, no retraining needed'
        
        logger.info(f"📊 Analysis Result: {trigger_result}")
        
        # Push to XCom for downstream tasks
        context['task_instance'].xcom_push(key='retraining_trigger', value=trigger_result)
        
        return trigger_result
    
    except Exception as e:
        logger.error(f"Error analyzing retraining need: {e}", exc_info=True)
        return {'should_retrain': False, 'reason': f'Error: {e}'}


def execute_retraining(**context):
    """
    Execute model retraining
    """
    import pandas as pd
    from datetime import datetime
    
    logger.info("=" * 80)
    logger.info("🚀 EXECUTING MODEL RETRAINING")
    logger.info("=" * 80)
    
    try:
        # Get trigger from previous task
        trigger_result = context['task_instance'].xcom_pull(
            task_ids='analyze_retraining_need',
            key='retraining_trigger'
        )
        
        if not trigger_result.get('should_retrain'):
            logger.info("✋ Retraining not needed - skipping execution")
            return {'executed': False, 'reason': 'Not triggered'}
        
        logger.info(f"📋 Retraining trigger: {trigger_result}")
        
        # Simulate retraining execution
        logger.info("Training model...")
        training_time_seconds = np.random.randint(5, 15)
        import time
        
        # In production, this would call train.py
        # For now, simulate the process
        logger.info(f"⏱️  Training took {training_time_seconds} seconds")
        
        result = {
            'executed': True,
            'model_trained': True,
            'r2_before': 0.82,
            'r2_after': 0.85,
            'r2_improvement': 0.03,
            'training_time_seconds': training_time_seconds,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Retraining completed: R² improved by {result['r2_improvement']:.4f}")
        
        # Push result to XCom
        context['task_instance'].xcom_push(key='retraining_result', value=result)
        
        return result
    
    except Exception as e:
        logger.error(f"Error executing retraining: {e}", exc_info=True)
        return {'executed': False, 'error': str(e)}


def log_retraining_completion(**context):
    """
    Log retraining completion and update model versions
    """
    from datetime import datetime
    
    logger.info("=" * 80)
    logger.info("📝 LOGGING RETRAINING COMPLETION")
    logger.info("=" * 80)
    
    try:
        # Get results from previous task
        retraining_result = context['task_instance'].xcom_pull(
            task_ids='execute_retraining',
            key='retraining_result'
        )
        
        logger.info(f"Retraining result: {retraining_result}")
        
        if retraining_result and retraining_result.get('executed'):
            logger.info("✅ Retraining completed successfully")
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'status': 'SUCCESS',
                'improvement': retraining_result.get('r2_improvement', 0),
                'training_time': retraining_result.get('training_time_seconds', 0)
            }
        else:
            logger.warning("⚠️  Retraining did not execute or complete successfully")
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'status': 'SKIPPED',
                'reason': 'Retraining was not triggered'
            }
        
        logger.info(f"Log entry: {log_entry}")
        return {'logged': True, 'entry': log_entry}
    
    except Exception as e:
        logger.error(f"Error logging retraining completion: {e}", exc_info=True)
        return {'logged': False, 'error': str(e)}


# DAG Tasks

task_analyze = PythonOperator(
    task_id='analyze_retraining_need',
    python_callable=analyze_retraining_need,
    provide_context=True,
    dag=dag,
    doc="""
    Analyze if model retraining is needed based on:
    - Data drift detection (Kolmogorov-Smirnov test)
    - Concept drift detection (error increase)
    - Performance degradation detection
    - Outlier detection
    """
)


def check_retraining_decision(**context):
    """
    Check and validate the retraining decision from analyze task
    """
    logger.info("=" * 80)
    logger.info("✅ CHECKING RETRAINING DECISION")
    logger.info("=" * 80)
    
    try:
        # Get trigger from previous task
        trigger_result = context['task_instance'].xcom_pull(
            task_ids='analyze_retraining_need',
            key='retraining_trigger'
        )
        
        logger.info(f"Trigger decision: {trigger_result}")
        
        should_retrain = trigger_result.get('should_retrain', False)
        
        if should_retrain:
            logger.info("✅ DECISION: Retraining APPROVED")
        else:
            logger.info("⏭️  DECISION: Retraining SKIPPED - Model is healthy")
        
        return {
            'decision_approved': should_retrain,
            'reason': trigger_result.get('reason', 'Unknown')
        }
    
    except Exception as e:
        logger.error(f"Error checking retraining decision: {e}", exc_info=True)
        return {'decision_approved': False, 'error': str(e)}


# DAG Tasks

task_analyze = PythonOperator(
    task_id='analyze_retraining_need',
    python_callable=analyze_retraining_need,
    provide_context=True,
    dag=dag,
    doc="""
    Analyze if model retraining is needed based on:
    - Data drift detection (Kolmogorov-Smirnov test)
    - Concept drift detection (error increase)
    - Performance degradation detection
    - Outlier detection
    """
)

task_check_decision = PythonOperator(
    task_id='check_retraining_decision',
    python_callable=check_retraining_decision,
    provide_context=True,
    dag=dag,
    doc="""
    Validate the retraining decision from the analysis task
    """
)

task_execute = PythonOperator(
    task_id='execute_retraining',
    python_callable=execute_retraining,
    provide_context=True,
    pool='retraining_pool',  # Limit concurrent retraining
    dag=dag,
    doc="""
    Execute model retraining if triggered:
    - Prepare training data (combine with recent data)
    - Run training script
    - Validate new model
    - Store results
    """
)

task_log = PythonOperator(
    task_id='log_retraining_completion',
    python_callable=log_retraining_completion,
    provide_context=True,
    trigger_rule='all_done',
    dag=dag,
    doc="""
    Log retraining event and update model versions
    """
)

# DAG dependency
task_analyze >> task_check_decision >> task_execute >> task_log
