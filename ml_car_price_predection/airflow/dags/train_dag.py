"""
Simple Airflow DAG that runs the training script.
Drop this DAG into an Airflow `dags/` folder after installing Airflow.
"""
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG('carprice_train_dag', default_args=default_args, schedule_interval='@daily', catchup=False) as dag:
    train = BashOperator(
        task_id='train_model',
        bash_command='python /opt/airflow/dags/ml_car_price_predection/train.py --n-samples 5000'
    )

    train
