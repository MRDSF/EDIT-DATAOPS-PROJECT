"""
DAG: news_pipeline
Schedule: Daily at 07:00 UTC
Pipeline: Scrape news → Load CSVs to PostgreSQL → Transform with dbt
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
    dag_id="news_pipeline",
    default_args=default_args,
    description="Daily Tesla news pipeline: Scrape → Load CSVs → Transform with dbt",
    schedule_interval="0 7 * * *",  # daily at 07:00 UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["news", "elt", "bronze", "silver", "gold", "scraping"],
) as dag:

    scrape_notateslaapp = BashOperator(
        task_id="scrape_notateslaapp",
        bash_command=f"cd {WORKSPACE}/extract && PYTHONPATH={WORKSPACE} python web_scrap_tesla_news_source1.py",
    )

    scrape_euronews = BashOperator(
        task_id="scrape_euronews",
        bash_command=f"cd {WORKSPACE}/extract && PYTHONPATH={WORKSPACE} python web_scrap_tesla_news_source2.py",
    )

    load_news_data = BashOperator(
        task_id="load_news_data",
        bash_command=f"cd {WORKSPACE}/load && PYTHONPATH={WORKSPACE} python load_news.py",
    )

    dbt_run_silver_news = BashOperator(
        task_id="dbt_run_silver_news",
        bash_command=(
            f"docker exec {DBT_CONTAINER} sh -c \""
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt run --select silver_news --profiles-dir {DBT_PROFILES_DIR}"
            "\""
        ),
    )

    dbt_run_gold_news = BashOperator(
        task_id="dbt_run_gold_news",
        bash_command=(
            f"docker exec {DBT_CONTAINER} sh -c \""
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt run --select gold_news_monthly_summary gold_news_info --profiles-dir {DBT_PROFILES_DIR}"
            "\""
        ),
    )

    dbt_test_news = BashOperator(
        task_id="dbt_test_news",
        bash_command=(
            f"docker exec {DBT_CONTAINER} sh -c \""
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt test --select silver_news gold_news_monthly_summary gold_news_info --profiles-dir {DBT_PROFILES_DIR}"
            "\""
        ),
    )

    (
        [scrape_notateslaapp, scrape_euronews]
        >> load_news_data
        >> dbt_run_silver_news
        >> dbt_run_gold_news
        >> dbt_test_news
    )
