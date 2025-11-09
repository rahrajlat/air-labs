"""
An example DAG that uses Cosmos to render a dbt project.
"""

import os
from datetime import datetime
from pathlib import Path

from cosmos import DbtDag, ProjectConfig, ProfileConfig
from cosmos.profiles import PostgresUserPasswordProfileMapping
from airflow.models.param import Param



profile_config = ProfileConfig(
    profile_name="dbt_warehouse_demo",
    target_name="dev",
    profile_mapping=PostgresUserPasswordProfileMapping(
        conn_id="airflow_postgres_db",
        profile_args={"schema": "core"},
    ),
)

# [START local_example]
basic_cosmos_dag = DbtDag(
    # dbt/cosmos-specific parameters
    project_config=ProjectConfig(
        "/opt/airflow/dbt/dbt_warehouse_demo_with_docs",
    ),
    profile_config=profile_config,
    operator_args={
        "install_deps": True,  # install any necessary dependencies before running any dbt command
        "full_refresh": True,  # used only in dbt commands that support this flag
    },
    # normal dag parameters
    start_date=datetime(2023, 1, 1),
    catchup=False,
    dag_id="dag_dbt_cosmos",
    default_args={"retries": 2},
    params={"dbt_project_dir": Param("/opt/airflow/dbt/dbt_warehouse_demo_with_docs", type="string")},
)
# [END local_example]