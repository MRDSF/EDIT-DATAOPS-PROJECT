"""
DAG: stock_pipeline
Schedule: Monthly (1st of each month)
Pipeline: Extract stock data from API → Load to PostgreSQL → Transform with dbt
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta


WORKSPACE = "/workspace"
DBT_CONTAINER = "dbt_to_postgres_dataops"
DBT_PROJECT_DIR = "/usr/app"
DBT_PROFILES_DIR = "/root/.dbt"

default_args = {
    "owner": "dataops",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "env": {
        "POSTGRES_HOST": "database",
        "POSTGRES_PORT": "5432",
    },
}

with DAG(
    dag_id="stock_pipeline",
    default_args=default_args,
    description="Monthly Tesla stock data pipeline: Extract → Load → Transform",
    schedule_interval="0 6 1 * *",  # 1st of each month at 06:00 UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["stocks", "elt", "bronze", "silver", "gold"],
) as dag:

    extract_stock_data = BashOperator(
        task_id="extract_stock_data",
        # PYTHONPATH is set to the workspace so that the script can import modules from the project if needed (e.g. from models.schemas import ApiResponse)
        bash_command=f"cd {WORKSPACE} && PYTHONPATH={WORKSPACE} python extract/collect_api_data.py", 
    )

    load_stock_data = BashOperator(
        task_id="load_stock_data",
        bash_command=f"cd {WORKSPACE}/load && python load_stocks.py",
    )

    dbt_run_silver_stock = BashOperator(
        task_id="dbt_run_silver_stock",
        bash_command=(
            f"docker exec {DBT_CONTAINER} sh -c \""
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt run --select silver_stock_data --profiles-dir {DBT_PROFILES_DIR}"
            "\""
        ),
    )

    dbt_run_gold_stock = BashOperator(
        task_id="dbt_run_gold_stock",
        bash_command=(
            f"docker exec {DBT_CONTAINER} sh -c \""
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt run --select gold_stock_monthly_summary --profiles-dir {DBT_PROFILES_DIR}"
            "\""
        ),
    )

    dbt_test_stock = BashOperator(
        task_id="dbt_test_stock",
        bash_command=(
            f"docker exec {DBT_CONTAINER} sh -c \""
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt test --select silver_stock_data gold_stock_monthly_summary --profiles-dir {DBT_PROFILES_DIR}"
            "\""
        ),
    )

    (
        extract_stock_data
        >> load_stock_data
        >> dbt_run_silver_stock
        >> dbt_run_gold_stock
        >> dbt_test_stock
    )
