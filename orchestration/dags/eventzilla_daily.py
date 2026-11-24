"""EventZilla daily pipeline: land -> Airbyte -> dbt -> data quality.

land_workbook ┐
              ├─> airbyte_sync -> dbt_build -> quality_raw (report) -> quality_star_schema (gate)
scrape_enrich ┘
"""

import os
import time
from datetime import datetime, timedelta

import requests
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

HOME = os.environ.get("EVENTZILLA_HOME", "/opt/eventzilla")
RUNTIME = "/opt/eventzilla-runtime"
AIRBYTE = os.environ.get("AIRBYTE_API", "http://host.docker.internal:8006/api/public/v1")
CONNECTION = "EventZilla landing → warehouse"


def airbyte_sync() -> None:
    """Run the Airbyte connection and wait for it (Airbyte public API)."""
    connections = requests.get(f"{AIRBYTE}/connections", timeout=30).json()["data"]
    connection_id = next(c["connectionId"] for c in connections if c["name"] == CONNECTION)
    job = requests.post(f"{AIRBYTE}/jobs", json={"connectionId": connection_id, "jobType": "sync"}, timeout=30)
    job.raise_for_status()
    job_id = job.json()["jobId"]
    while True:
        status = requests.get(f"{AIRBYTE}/jobs/{job_id}", timeout=30).json()["status"]
        print(f"Airbyte job {job_id}: {status}")
        if status == "succeeded":
            return
        if status in ("failed", "cancelled", "incomplete"):
            raise RuntimeError(f"Airbyte job {job_id} ended {status}")
        time.sleep(15)


with DAG(
    dag_id="eventzilla_daily",
    description="Land the sources, load them with Airbyte, build the star with dbt, check it with Great Expectations",
    start_date=datetime(2026, 11, 1),
    schedule="0 5 * * *",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=5)},
    tags=["eventzilla", "warehouse"],
) as dag:
    land = BashOperator(task_id="land_workbook", bash_command=f"python {HOME}/ingestion/land_workbook.py --s3")
    enrich = BashOperator(task_id="scrape_enrichment",
                          bash_command=f"python {HOME}/ingestion/scrape_enrichment.py --s3")
    load = PythonOperator(task_id="airbyte_sync", python_callable=airbyte_sync)
    dbt = BashOperator(
        task_id="dbt_build",
        bash_command=(f"/opt/dbt/bin/dbt build --project-dir {HOME}/transformation --profiles-dir {HOME}/transformation"
                      f" --log-path {RUNTIME}/dbt-logs"),
        env={"DBT_TARGET_PATH": f"{RUNTIME}/dbt-target"}, append_env=True,
    )
    gx_env = {"GX_PROJECT_DIR": f"{RUNTIME}/gx", "GX_DOCS_DIR": f"{RUNTIME}/data_docs"}
    quality_raw = BashOperator(task_id="quality_raw", env=gx_env, append_env=True,
                               bash_command=f"/opt/gx/bin/python {HOME}/quality/validate.py raw")
    quality_star = BashOperator(task_id="quality_star_schema", env=gx_env, append_env=True,
                                bash_command=f"/opt/gx/bin/python {HOME}/quality/validate.py star_schema")

    [land, enrich] >> load >> dbt >> quality_raw >> quality_star
