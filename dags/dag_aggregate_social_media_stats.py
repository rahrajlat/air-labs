
from __future__ import annotations
import random, time, pendulum
from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

START_DATE = pendulum.datetime(2024, 1, 1, tz="UTC")

def random_sleep():
    time.sleep(25)

def maybe_fail():
    if random.random() < 0.3:
        raise Exception("Random failure for testing")
    print("Success")

with DAG(
    dag_id="dag_aggregate_social_media_stats",
    start_date=START_DATE,
    schedule="@daily",
    catchup=False,
    dagrun_timeout=timedelta(minutes=30),
    tags=['social', 'analytics'],
) as dag:
    start = EmptyOperator(task_id="start")
    task1 = PythonOperator(task_id="random_sleep", python_callable=random_sleep)
    task2 = PythonOperator(task_id="maybe_fail", python_callable=maybe_fail)
    long_run = BashOperator(task_id="long_run", bash_command="sleep { 5 * (execution_date.day % 10 + 1) }")
    end = EmptyOperator(task_id="end")
    start >> task1 >> [task2, long_run] >> end
