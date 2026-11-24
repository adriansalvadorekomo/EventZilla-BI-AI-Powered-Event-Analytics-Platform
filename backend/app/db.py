"""Warehouse access, always as the read-only role analyst_ro."""

import datetime as dt
import decimal
import os
from functools import cache

from sqlalchemy import create_engine, text


@cache
def engine():
    e = os.environ
    return create_engine(
        f"postgresql+psycopg2://analyst_ro:{e['ANALYST_DB_PASSWORD']}@{e.get('EVENTZILLA_DB_HOST', 'localhost')}"
        f":{e.get('EVENTZILLA_DB_PORT', '5442')}/{e.get('EVENTZILLA_DB_NAME', 'eventzilla')}",
        pool_pre_ping=True, pool_size=5)


def _plain(value):
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return value


def run_readonly(sql: str, params: dict | None = None) -> tuple[list[str], list[list]]:
    with engine().connect() as conn:
        result = conn.execute(text(sql), params or {})
        columns = list(result.keys())
        return columns, [[_plain(v) for v in row] for row in result]


def records(sql: str, params: dict | None = None) -> list[dict]:
    columns, rows = run_readonly(sql, params)
    return [dict(zip(columns, row, strict=True)) for row in rows]
