"""Airbyte as code: the S3 landing bucket -> the warehouse's raw schema, one stream per entity.

    AIRBYTE_API=http://localhost:8006/api/public/v1 python ingestion/airbyte/setup_airbyte.py [--sync]

Idempotent: source, destination and connection are found by name and updated, never duplicated. With --sync it
also runs the connection once and waits for it (Airflow does the same daily, task airbyte_sync).
Airbyte runs in its own cluster (abctl); it reaches the landing store and the warehouse by their container names
on the cluster's Docker network (compose.yaml attaches both to it).
"""

import argparse
import os
import sys
import time

import requests

API = os.environ.get("AIRBYTE_API", "http://localhost:8006/api/public/v1").rstrip("/")
SOURCE, DESTINATION, CONNECTION = "EventZilla landing (S3)", "EventZilla warehouse (raw)", "EventZilla landing → warehouse"
ENTITIES = ["beneficiary", "provider", "category", "subcategory", "category_service", "service", "event",
            "reservation", "evaluation", "complaint", "site_traffic", "marketing_spend", "competitor", "location",
            "season", "platform_review", "tn_governorate", "tn_holiday"]


def call(method: str, path: str, **kw):
    r = requests.request(method, f"{API}{path}", timeout=900, **kw)  # source checks start a connector pod
    if r.status_code >= 400:
        sys.exit(f"{method} {path}: {r.status_code} {r.text[:400]}")
    return r.json() if r.text else None


def upsert(kind: str, name: str, body: dict) -> str:
    """Create or update a source / destination / connection by name; return its id."""
    key = {"sources": "sourceId", "destinations": "destinationId", "connections": "connectionId"}[kind]
    for item in call("GET", f"/{kind}", params={"limit": 100})["data"]:
        if item["name"] == name:
            call("PATCH", f"/{kind}/{item[key]}", json=body)
            return item[key]
    return call("POST", f"/{kind}", json={"name": name, **body})[key]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sync", action="store_true", help="run the connection once and wait for it")
    args = parser.parse_args()
    workspace = call("GET", "/workspaces")["data"][0]["workspaceId"]

    source = upsert("sources", SOURCE, {"workspaceId": workspace, "configuration": {
        "sourceType": "s3",
        "bucket": os.environ.get("LANDING_BUCKET", "landing"),
        "endpoint": os.environ.get("AIRBYTE_S3_ENDPOINT", "http://eventzilla-landing-1:8333"),
        "credentials": {"auth_type": "iam_user", "aws_access_key_id": os.environ["LANDING_ACCESS_KEY"],
                        "aws_secret_access_key": os.environ["LANDING_SECRET_KEY"]},
        "region_name": "us-east-1",  # SeaweedFS ignores it; the connector wants one
        # every value lands as text, exactly as in the source file; dbt types and cleans it
        "streams": [{"name": e, "globs": [f"eventzilla/{e}/*.csv"], "validation_policy": "Emit Record",
                     "format": {"filetype": "csv", "inference_type": "None"}} for e in ENTITIES],
    }})
    destination = upsert("destinations", DESTINATION, {"workspaceId": workspace, "configuration": {
        "destinationType": "postgres",
        "host": os.environ.get("AIRBYTE_WAREHOUSE_HOST", "eventzilla-warehouse-1"), "port": 5432,
        "database": "eventzilla", "schema": "raw",
        "username": os.environ.get("WAREHOUSE_USER", "eventzilla"), "password": os.environ["WAREHOUSE_PASSWORD"],
        "ssl_mode": {"mode": "disable"}, "tunnel_method": {"tunnel_method": "NO_TUNNEL"},
    }})
    connection = upsert("connections", CONNECTION, {
        "sourceId": source, "destinationId": destination,
        "namespaceDefinition": "destination", "schedule": {"scheduleType": "manual"},  # Airflow schedules it
        "configurations": {"streams": [{"name": e, "syncMode": "full_refresh_overwrite"} for e in ENTITIES]},
    })
    print(f"source {source}\ndestination {destination}\nconnection {connection}")

    if args.sync:
        job = call("POST", "/jobs", json={"connectionId": connection, "jobType": "sync"})["jobId"]
        while (status := call("GET", f"/jobs/{job}")["status"]) in ("pending", "running"):
            time.sleep(15)
        info = call("GET", f"/jobs/{job}")
        print(f"sync job {job}: {status} · {info.get('rowsSynced')} rows · {info.get('duration')}")
        sys.exit(0 if status == "succeeded" else 1)


if __name__ == "__main__":
    main()
