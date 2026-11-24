"""Shared helpers for the data-science objectives: warehouse connection and report writing."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

REPORTS = Path(__file__).resolve().parent / "reports"


def engine():
    e = os.environ
    return create_engine(
        f"postgresql+psycopg2://{e.get('WAREHOUSE_USER', 'eventzilla')}:{e['WAREHOUSE_PASSWORD']}"
        f"@{e.get('EVENTZILLA_DB_HOST', 'localhost')}:{e.get('EVENTZILLA_DB_PORT', e.get('WAREHOUSE_PORT', '5442'))}"
        f"/{e.get('EVENTZILLA_DB_NAME', 'eventzilla')}")


def query(sql: str) -> pd.DataFrame:
    with engine().connect() as conn:
        return pd.read_sql(text(sql), conn)


def write_report(name: str, report: dict) -> Path:
    """Reports are JSON, committed: they are the evidence the API and the documentation quote."""
    REPORTS.mkdir(exist_ok=True)
    report = {"generated_at": datetime.now(UTC).isoformat(timespec="seconds"), **report}
    path = REPORTS / f"{name}.json"
    path.write_text(json.dumps(report, indent=2, default=str) + "\n")
    return path
