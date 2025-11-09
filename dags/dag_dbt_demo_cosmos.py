from __future__ import annotations
import os
import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator

# Paths
DBT_PROJECT_DIR  = os.getenv("DBT_PROJECT_DIR", "/opt/airflow/dbt/dbt_warehouse_demo_with_docs")
DBT_PROFILES_DIR = os.getenv("DBT_PROFILES_DIR", "/opt/airflow/dbt/dbt_warehouse_demo_with_docs")

default_args = {
    "owner": "airflow",
    "retries": 1,
}

with DAG(
    dag_id="dag_dbt_demo_simple",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
    tags=["dbt", "bash", "postgres"],
    default_args=default_args,
) as dag:

    # 1️⃣ Compile models (optional but good for validation)
    dbt_compile = BashOperator(
        task_id="dbt_compile",
        bash_command=f"""
        cd {DBT_PROJECT_DIR} &&
        dbt compile --profiles-dir {DBT_PROFILES_DIR}
        """,
    )

    # 2️⃣ Run the actual transformations (build models + tests)
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"""
        cd {DBT_PROJECT_DIR} &&
        dbt build --profiles-dir {DBT_PROFILES_DIR}
        """,
    )

    # 3️⃣ Optional: run docs generation
    dbt_docs = BashOperator(
        task_id="dbt_docs",
        bash_command=f"""
        cd {DBT_PROJECT_DIR} &&
        dbt docs generate --profiles-dir {DBT_PROFILES_DIR}
        """,
    )

    dbt_compile >> dbt_build >> dbt_docs