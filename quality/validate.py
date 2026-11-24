"""Data governance checkpoints (Great Expectations), run by Airflow after dbt.

    python quality/validate.py raw            # report: what arrived from the sources (never blocks)
    python quality/validate.py star_schema    # gate: the contract of the star (exit 1 if broken)

Both write Data Docs to $GX_DOCS_DIR (default quality/uncommitted/data_docs). The raw checkpoint documents the
known defects of the source, which dbt quarantines in the quality schema; the star_schema checkpoint is what the
dashboards rely on.
"""

import os
import sys
from pathlib import Path

import great_expectations as gx
import great_expectations.expectations as gxe
import sqlalchemy as sa

HERE = Path(__file__).resolve().parent
RESERVATIONS_IN_SOURCE = 18000  # rows of the RESERVATION sheet, checked again against raw at run time


def warehouse_url() -> str:
    e = os.environ
    return (f"postgresql+psycopg2://{e.get('EVENTZILLA_DB_USER', 'eventzilla')}:{e['EVENTZILLA_DB_PASSWORD']}"
            f"@{e.get('EVENTZILLA_DB_HOST', 'localhost')}:{e.get('EVENTZILLA_DB_PORT', '5442')}"
            f"/{e.get('EVENTZILLA_DB_NAME', 'eventzilla')}")


# table -> expectations. (schema, table): [expectation, ...]
RAW = {
    ("raw", "reservation"): [
        gxe.ExpectTableRowCountToEqual(value=RESERVATIONS_IN_SOURCE),
        gxe.ExpectColumnValuesToBeUnique(column="id_reservation"),
        gxe.ExpectColumnValuesToBeInSet(column="status", value_set=["confirmed", "pending", "cancelled"]),
    ],
    ("raw", "evaluation"): [
        # known defect: the source also holds ratings of 6, 9, 12 and 15
        gxe.ExpectColumnValuesToBeInSet(column="rating", value_set=["1", "2", "3", "4", "5"]),
    ],
    ("raw", "marketing_spend"): [
        # known defect: '2024-24' and other non-months
        gxe.ExpectColumnValuesToMatchRegex(column="month", regex=r"^[0-9]{4}-(0[1-9]|1[0-2])$"),
    ],
    ("raw", "beneficiary"): [
        gxe.ExpectColumnValuesToBeUnique(column="id_beneficiary"),
        gxe.ExpectColumnValuesToMatchRegex(column="email", regex=r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", mostly=0.9),
    ],
}

STAR = {
    ("marts", "fact_reservation"): [
        gxe.ExpectTableRowCountToEqual(value=RESERVATIONS_IN_SOURCE),      # no reservation lost (v1 kept 428)
        gxe.ExpectColumnValuesToBeUnique(column="reservation_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="event_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="service_id"),
        gxe.ExpectColumnValuesToBeBetween(column="revenue", min_value=0),
        gxe.ExpectColumnValuesToBeBetween(column="rating_avg", min_value=1, max_value=5),
        gxe.ExpectColumnValuesToBeInSet(column="status", value_set=["confirmed", "pending", "cancelled"]),
    ],
    ("marts", "dim_date"): [
        gxe.ExpectTableRowCountToEqual(value=1461),                        # 2022-01-01 .. 2025-12-31, no gap
        gxe.ExpectColumnValuesToBeUnique(column="date_day"),
        gxe.ExpectColumnValuesToNotBeNull(column="season"),
    ],
    ("marts", "dim_beneficiary"): [
        gxe.ExpectColumnValuesToBeUnique(column="beneficiary_id"),
        # governance: a whitelist of columns, so no personal data (names, e-mails, phones) can reach the marts
        gxe.ExpectTableColumnsToMatchSet(column_set=["beneficiary_id", "email_domain", "events", "first_event_date",
                                                     "is_returning", "complaints"], exact_match=True),
    ],
    ("marts", "dim_provider"): [gxe.ExpectColumnValuesToBeUnique(column="provider_id")],
    ("marts", "dim_service"): [gxe.ExpectColumnValuesToBeUnique(column="service_id")],
    ("marts", "dim_event"): [gxe.ExpectColumnValuesToBeUnique(column="event_id")],
}

CHECKPOINTS = {"raw": RAW, "star_schema": STAR}


def run(name: str) -> bool:
    # GX keeps its config in a project folder; Airflow points it at a writable runtime volume
    context = gx.get_context(mode="file", project_root_dir=os.environ.get("GX_PROJECT_DIR", str(HERE)))
    docs_dir = Path(os.environ.get("GX_DOCS_DIR", HERE / "uncommitted" / "data_docs"))
    site = "eventzilla"
    if site not in context.get_site_names():
        context.add_data_docs_site(site_name=site, site_config={
            "class_name": "SiteBuilder",
            "store_backend": {"class_name": "TupleFilesystemStoreBackend", "base_directory": str(docs_dir)},
            "site_index_builder": {"class_name": "DefaultSiteIndexBuilder"},
        })
    source = context.data_sources.add_or_update_postgres(name="warehouse", connection_string=warehouse_url())
    definitions = []
    for (schema, table), expectations in CHECKPOINTS[name].items():
        asset_name = f"{schema}.{table}"
        try:
            asset = source.get_asset(asset_name)
        except LookupError:
            asset = source.add_table_asset(name=asset_name, table_name=table, schema_name=schema)
        try:
            batch = asset.get_batch_definition("whole table")
        except KeyError:
            batch = asset.add_batch_definition_whole_table("whole table")
        suite = context.suites.add_or_update(gx.ExpectationSuite(name=f"{name}.{asset_name}"))
        for expectation in expectations:
            suite.add_expectation(expectation)
        suite.save()
        definitions.append(context.validation_definitions.add_or_update(
            gx.ValidationDefinition(name=f"{name}.{asset_name}", data=batch, suite=suite)))
    checkpoint = context.checkpoints.add_or_update(gx.Checkpoint(
        name=name, validation_definitions=definitions,
        actions=[gx.checkpoint.UpdateDataDocsAction(name="data_docs", site_names=[site])]))
    result = checkpoint.run()
    for run_result in result.run_results.values():
        stats = run_result.statistics
        print(f"{run_result.suite_name:48} {stats['successful_expectations']}/{stats['evaluated_expectations']} passed")
    print(f"checkpoint {name}: {'PASSED' if result.success else 'FAILED'} · Data Docs in {docs_dir}")
    stats = [r.statistics for r in result.run_results.values()]
    record(name, result.success, sum(s["successful_expectations"] for s in stats),
           sum(s["evaluated_expectations"] for s in stats))
    return result.success


def record(name: str, passed: bool, checks_passed: int, checks: int) -> None:
    """Keep every result in the warehouse, so the application can say when the figures last passed the gate."""
    engine = sa.create_engine(warehouse_url())
    with engine.begin() as conn:
        conn.execute(sa.text("""create table if not exists quality.gate_runs (
            checkpoint text not null, passed boolean not null, checks_passed int not null, checks int not null,
            run_at timestamptz not null default now())"""))
        conn.execute(sa.text("""insert into quality.gate_runs (checkpoint, passed, checks_passed, checks)
                               values (:checkpoint, :passed, :ok, :n)"""),
                     {"checkpoint": name, "passed": passed, "ok": checks_passed, "n": checks})


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "star_schema"
    ok = run(name)
    # the raw checkpoint reports the source's known defects; only the star schema gates the pipeline
    sys.exit(0 if ok or name == "raw" else 1)
