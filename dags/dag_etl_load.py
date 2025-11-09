# dags/etl_dummy.py
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
from airflow.exceptions import AirflowRescheduleException
from airflow.models import Variable
from airflow.utils import timezone

from airflow.utils.state import State
from airflow.utils.session import provide_session
from airflow.models.taskinstance import TaskInstance
from airflow.operators.python import PythonOperator
import time


def python_task():
    time.sleep(5)
    print("This is a simple Python task.")


default_args = {
    "owner": "data_eng",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
}

with DAG(
    dag_id="dag_etl_load",
    description="Simple ETL-style DAG using only dummy tasks",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["example", "etl", "dummy"],
) as dag:

    # Define ETL pipeline stages
    start = EmptyOperator(task_id="start")

    extract = PythonOperator(
        task_id="extract", python_callable=python_task, retries=2)
    transform = EmptyOperator(task_id="transform")
    load = EmptyOperator(task_id="load")
    dq_check = EmptyOperator(task_id="data_quality_check")

    end = EmptyOperator(task_id="end")

    # Define DAG dependencies
    start >> extract >> transform >> load >> dq_check >> end
