"""Draw the diagrams of the EventZilla data platform (docs/diagrams/c4/*.svg).

Four views, each in a light and a dark theme:
  c4-context     C4 level 1: who uses the platform, what it depends on
  c4-container   C4 level 2: the Compose stack (compose.yaml) and Airbyte beside it
  c4-pipeline    the daily run, from the sources to the gate and the readers
  c4-star        the star schema: one fact, six dimensions, the keys between them

Every element comes from the repository: compose.yaml, orchestration/dags/eventzilla_daily.py, ingestion/,
transformation/models/marts/, quality/validate.py, backend/, frontend/, automation/n8n/, monitoring/.
Drawing kit: c4kit.py (same engine as the Episteme diagrams).

    uv run --no-project --with fonttools --with brotli python docs/diagrams/c4/build_c4.py [--png]
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from c4kit import Box, Canvas, View, build  # noqa: E402

READOUT = [("RESERVATIONS KEPT", "18,000 of 18,000"), ("DBT", "79 nodes pass"), ("GATE", "15 of 15")]


# ── C4 level 1 · context ───────────────────────────────────────────────────
def context_view(cv: Canvas):
    managers = Box(32, 184, 208, 112)
    team = Box(32, 472, 208, 112)
    system = Box(376, 184, 512, 400)
    ext_x, ext_w = 1032, 216
    source = Box(ext_x, 184, ext_w, 88)
    firecrawl = Box(ext_x, 288, ext_w, 88)
    groq = Box(ext_x, 392, ext_w, 88)

    cv.arrow([(managers.r, managers.cy), (system.x, managers.cy)])
    cv.label([("read, ask", False), ("app · Metabase", True)], 308, managers.cy - 34)
    cv.arrow([(team.r, team.cy), (system.x, team.cy)])
    cv.label([("run, check", False), ("mise · Airflow", True)], 308, team.cy - 34)

    cv.arrow([(source.x, source.cy), (system.r, source.cy)])
    cv.label([("exports", False), ("16-sheet workbook", True)], 960, source.cy - 34)
    cv.arrow([(system.r, firecrawl.cy), (firecrawl.x, firecrawl.cy)])
    cv.label([("scrapes", False), ("Wikipedia pages", True)], 960, firecrawl.cy - 34)
    cv.arrow([(system.r, groq.cy), (groq.x, groq.cy)])
    cv.label([("screens, writes", False), ("one SELECT", True)], 960, groq.cy - 34)

    cv.node(managers, "person", "Person", "Managers", None, ["Read the four objectives,", "ask the analyst"], ["user"])
    cv.node(team, "person", "Person", "Data team", None, ["Runs the pipeline and", "watches the gate"], ["user"])
    cv.node(system, "container", "Software system", "EventZilla data platform", "Airbyte · dbt · GX · Airflow",
            ["Lands the company's workbook and public reference", "pages, rebuilds one star schema every morning and",
             "checks it before anyone reads it.", "",
             "Managers read the four business objectives in an", "analysis app and in Metabase, and ask an analyst",
             "that answers from the warehouse, read-only.", "",
             "n8n alerts when the figures are stale or fail the", "gate, and writes a weekly decision brief."],
            ["apacheairflow", "postgresql", "metabase", "angular"], focal=True)
    cv.node(source, "external", "External", "EventZilla operations", "the source workbook", [], ["file"])
    cv.node(firecrawl, "external", "External", "Firecrawl", "governorates, holidays", [], ["world"])
    cv.node(groq, "external", "External", "Groq", "gpt-oss-120b", [], ["terminal"])

    cv.readout(READOUT, 1248, 96)
    cv.legend(632, [("person", "person"), ("focal", "the system"), ("external", "external system"),
                    ("call", "uses")])


# ── C4 level 2 · containers ────────────────────────────────────────────────
def container_view(cv: Canvas):
    w = 248
    xs = [32, 344, 656, 1000]
    ra, rb, rc, rd = 352, 560, 768, 976
    managers = Box(xs[0], 168, w, 96)
    frontend = Box(xs[0], ra, w, 128)
    api = Box(xs[1], ra, w, 128)
    metabase = Box(xs[2], ra, w, 128)
    groq = Box(xs[3], ra, w, 128)
    grafana = Box(xs[0], rb, w, 128)
    prom = Box(xs[1], rb, w, 128)
    n8n = Box(xs[2], rb, w, 128)
    firecrawl = Box(xs[3], rb, w, 128)
    dw = Box(xs[0], rc, 528, 128)
    airflow = Box(xs[2], rc, w, 128)
    airbyte = Box(xs[3], rc, w, 128)
    landing = Box(xs[2], rd, w, 128)

    cv.zone(Box(16, 312, 920, 880), "EVENTZILLA", "docker compose · compose.yaml", at="bottom", lx=200)

    cv.arrow([(managers.cx, managers.b), (managers.cx, frontend.y)])
    cv.label([("browser · :4200", True)], managers.cx + 12, 292, "start")
    cv.arrow([(managers.r, 200), (metabase.cx, 200), (metabase.cx, metabase.y)])
    cv.label([("dashboards · :3001", True)], 540, 188)
    cv.arrow([(frontend.r, 416), (api.x, 416)])
    cv.label([("/api", True)], 312, 404)
    cv.arrow([(api.cx + 60, api.y), (api.cx + 60, 332), (groq.cx, 332), (groq.cx, groq.y)])
    cv.label([("screen, write SQL", False)], 1068, 324)
    cv.arrow([(prom.cx, prom.y), (prom.cx, api.b)])
    cv.label([("/metrics", True)], prom.cx + 12, 532, "start")
    cv.arrow([(grafana.r, 624), (prom.x, 624)])
    cv.arrow([(n8n.x + 40, n8n.y), (n8n.x + 40, 520), (api.r - 40, 520), (api.r - 40, api.b)])
    cv.label([("HTTP", True)], 624, 508)
    cv.arrow([(api.x + 40, api.b), (api.x + 40, 536), (312, 536), (312, dw.y)])
    cv.label([("read-only role", True)], 324, 744, "start")
    cv.arrow([(metabase.r, 416), (920, 416), (920, 744), (dw.r - 32, 744), (dw.r - 32, dw.y)])
    cv.label([("SQL", True)], 760, 732)
    cv.arrow([(airflow.x, airflow.cy), (dw.r, airflow.cy)])
    cv.label([("dbt · GX", True)], 608, airflow.cy - 12)
    cv.arrow([(airflow.cx, airflow.b), (airflow.cx, landing.y)])
    cv.label([("lands files", False)], airflow.cx + 12, 940, "start")
    cv.arrow([(airflow.r, 800), (960, 800), (960, firecrawl.cy), (firecrawl.x, firecrawl.cy)])
    cv.label([("monthly", False)], 968, 724, "start")
    cv.arrow([(airflow.r, 864), (airbyte.x, 864)])
    cv.arrow([(airbyte.cx, airbyte.b), (airbyte.cx, landing.cy), (landing.r, landing.cy)])
    cv.label([("reads S3", False)], 1036, landing.cy - 12, "start")
    cv.arrow([(airbyte.x + 20, airbyte.b), (airbyte.x + 20, 1144), (dw.cx, 1144), (dw.cx, dw.b)])
    cv.label([("loads raw", False)], 560, 1132)

    cv.node(managers, "person", "Person", "Managers", None, ["Analysis app and Metabase"], ["user"])
    cv.node(frontend, "container", "Container", "Analysis app", "Angular 22 · nginx · :4200",
            ["Board, objective pages,", "the analyst"], ["angular", "nginx"])
    cv.node(api, "container", "Container", "API", "FastAPI · :8000",
            ["Indicators, questions,", "/api/ask, /metrics"], ["fastapi"])
    cv.node(metabase, "container", "Container", "Metabase", "Metabase · :3001",
            ["5 dashboards as code,", "one per objective"], ["metabase"])
    cv.node(groq, "external", "External", "Groq", "Prompt Guard · gpt-oss-120b",
            ["Screens the question,", "writes one SELECT"], ["terminal"])
    cv.node(grafana, "container", "Container", "Grafana", "Grafana · :3000",
            ["API and analyst", "dashboard, PromQL"], ["grafana"])
    cv.node(prom, "container", "Container", "Prometheus", "Prometheus · :9090",
            ["Scrapes the API;", "4 alert rules"], ["prometheus"])
    cv.node(n8n, "container", "Container", "n8n", "n8n · :5678 · automation/n8n",
            ["Freshness watch, weekly", "brief, ask webhook"], ["n8n"])
    cv.node(firecrawl, "external", "External", "Firecrawl", "scrape API · Wikipedia",
            ["Governorates and", "public holidays"], ["world"])
    cv.node(dw, "store", "Data store", "Warehouse", "PostgreSQL 16 · one server, one database per tool",
            ["raw (Airbyte) → staging → marts: the star schema, reporting, quality (quarantine,",
             "gate log). The API reads it as analyst_ro, which cannot write or see personal data."],
            ["postgresql"], focal=True)
    cv.node(airflow, "container", "Container", "Airflow", "Airflow 2.10 · :8080",
            ["Daily 05:00: lands, scrapes,", "syncs, builds, checks"], ["apacheairflow"])
    cv.node(airbyte, "container", "Container · abctl", "Airbyte", "Airbyte 2.5 · :8006",
            ["S3 source → Postgres", "destination, raw schema"], ["airbyte"], dashed=True)
    cv.node(landing, "store", "Data store", "Landing bucket", "SeaweedFS · S3 API · :8333",
            ["Workbook CSVs and", "scraped reference pages"], ["bucket"])

    cv.readout(READOUT, 1248, 96)
    cv.legend(1200, [("person", "person"), ("container", "container"), ("focal", "the warehouse"),
                     ("store", "data store"), ("external", "external"), ("call", "call / read / write")])


# ── the daily run, sources to readers ──────────────────────────────────────
def pipeline_view(cv: Canvas):
    w = 248
    xs = [32, 354, 676, 1000]
    r1, r2 = 200, 456
    sources = Box(xs[0], r1, w, 128)
    landing = Box(xs[1], r1, w, 128)
    airbyte = Box(xs[2], r1, w, 128)
    raw = Box(xs[3], r1, w, 128)
    dbt = Box(xs[3], r2, w, 128)
    star = Box(xs[2], r2, w, 128)
    gate = Box(xs[1], r2, w, 128)
    readers = Box(xs[0], r2, w, 128)

    cv.arrow([(sources.r, 264), (landing.x, 264)])
    cv.label([("land", False)], 317, 252)
    cv.arrow([(landing.r, 264), (airbyte.x, 264)])
    cv.label([("S3", True)], 637, 252)
    cv.arrow([(airbyte.r, 264), (raw.x, 264)])
    cv.label([("load", False)], 962, 252)
    cv.arrow([(raw.cx, raw.b), (raw.cx, dbt.y)])
    cv.label([("dbt build", True)], raw.cx + 12, 400, "start")
    cv.arrow([(dbt.x, 520), (star.r, 520)])
    cv.label([("43 tests", True)], 962, 508)
    cv.arrow([(star.x, 520), (gate.r, 520)])
    cv.label([("checked", False)], 637, 508)
    cv.arrow([(gate.x, 520), (readers.r, 520)])
    cv.label([("15 of 15", True)], 315, 508)

    cv.node(sources, "store", "Sources", "Workbook + web", "16 sheets · Firecrawl",
            ["Company exports, governorates", "and holidays from Wikipedia"], ["file", "world"])
    cv.node(landing, "store", "Data store", "Landing bucket", "SeaweedFS · S3",
            ["One CSV per entity,", "kept as received"], ["bucket"])
    cv.node(airbyte, "container", "Airbyte", "Extract and load", "S3 → PostgreSQL",
            ["18 streams, full refresh,", "33–35 s per sync"], ["airbyte"])
    cv.node(raw, "store", "Data store", "raw schema", "PostgreSQL · as loaded",
            ["One table per stream,", "nothing changed yet"], ["postgresql"])
    cv.node(dbt, "container", "dbt", "Transform and test", "36 models · 43 tests",
            ["Typed staging, quarantine,", "the star, reporting"], ["layers"])
    cv.node(star, "store", "Data store", "Star schema", "marts · reporting · quality",
            ["1 fact, 6 dimensions;", "defects counted, not hidden"], ["postgresql"])
    cv.node(gate, "container", "Great Expectations", "The gate", "star_schema checkpoint",
            ["18,000 rows kept, keys", "unique, no personal data"], ["shield"], focal=True)
    cv.node(readers, "external", "Readers", "App, analyst, Metabase", "and n8n's brief",
            ["Only figures that", "passed the gate"], ["angular", "metabase"])

    cv.readout([("ROWS LOADED", "55,260"), ("DAILY RUN", "about 60 s"), ("ORCHESTRATION", "Airflow · 05:00")],
               1248, 96)
    cv.legend(704, [("store", "data"), ("container", "step"), ("focal", "the gate"), ("external", "readers"),
                    ("call", "data flow")])


# ── the star schema ────────────────────────────────────────────────────────
def star_view(cv: Canvas):
    dw, dh = 280, 152
    left_x, right_x = 48, 952
    rows = [200, 400, 600]
    fact = Box(500, 200, 280, 552)
    dims_left = [Box(left_x, y, dw, dh) for y in rows]
    dims_right = [Box(right_x, y, dw, dh) for y in rows]

    keys_left = [[("reservation_date", True), ("event_date", True)], [("event_id", True)],
                 [("beneficiary_id", True)]]
    keys_right = [[("service_id", True)], [("provider_id", True)], [("governorate_id", True)]]
    for d, k in zip(dims_left, keys_left, strict=True):
        cv.arrow([(fact.x, d.cy), (d.r, d.cy)])
        cv.label(k, (d.r + fact.x) / 2, d.cy - 12 - 16 * (len(k) - 1))
    for d, k in zip(dims_right, keys_right, strict=True):
        cv.arrow([(fact.r, d.cy), (d.x, d.cy)])
        cv.label(k, (fact.r + d.x) / 2, d.cy - 12)

    cv.node(fact, "store", "Fact · one reservation", "fact_reservation", "18,000 rows · 2022–2025",
            ["Keys: event, service, provider,", "customer, governorate; the", "reservation and the event date.", "",
             "Measures: final_price,", "list_price, revenue (confirmed", "reservations only), rating_avg,",
             "evaluations.", "",
             "Status: confirmed, pending or", "cancelled. lead_time_days is", "kept but never charted.", "",
             "Tested: reservation_id unique,", "11 keys resolve, no reservation", "lost, revenue never negative,",
             "ratings within 1 to 5."],
            ["postgresql"], focal=True)
    specs_left = [
        ("dim_date", "1,461 days · role-played", ["Season, weekend, public", "holiday, Ramadan"]),
        ("dim_event", "event_id", ["Event type, budget,", "event date"]),
        ("dim_beneficiary", "beneficiary_id", ["Events, returning, complaints;", "no personal data"]),
    ]
    specs_right = [
        ("dim_service", "service_id", ["Service category,", "list price"]),
        ("dim_provider", "provider_id", ["Service type, city,", "complaints open"]),
        ("dim_geography", "governorate_id", ["24 governorates, 6 regions,", "population 2024 (Firecrawl)"]),
    ]
    for b, (title, tech, desc) in zip(dims_left + dims_right, specs_left + specs_right, strict=True):
        cv.node(b, "container", "Dimension", title, tech, desc)

    cv.readout([("FACT", "18,000 rows"), ("DIMENSIONS", "6"), ("RELATIONSHIP TESTS", "11")], 1232, 96)
    cv.legend(800, [("focal", "the fact"), ("container", "dimension"), ("call", "key: fact → dimension")])


VIEWS = [
    View("context", context_view, 1280, 740, "c4 model · level 1 · system context", "EventZilla data platform",
         "one star schema, checked before anyone reads it",
         "EventZilla data platform — C4 system context",
         "C4 context diagram: managers read the four business objectives in an analysis app and Metabase and ask "
         "an analyst; the data team runs the pipeline with mise and Airflow. The platform takes the company's "
         "16-sheet workbook, scrapes governorates and public holidays from Wikipedia with Firecrawl, and asks Groq "
         "to screen questions and write one SELECT."),
    View("container", container_view, 1280, 1280, "c4 model · level 2 · containers", "The Compose stack",
         "nine services around one warehouse, Airbyte beside them",
         "EventZilla data platform — C4 container view",
         "C4 container diagram: managers open the Angular analysis app, which calls the FastAPI service; the API "
         "asks Groq to screen questions and write SQL, and reads the PostgreSQL warehouse as a read-only role. "
         "Metabase reads the warehouse for the dashboards. Prometheus scrapes the API and Grafana reads Prometheus; "
         "n8n calls the API. Airflow lands the files in the SeaweedFS bucket, scrapes Firecrawl monthly, triggers "
         "Airbyte (installed beside the stack with abctl), which reads the bucket and loads the raw schema, then "
         "runs dbt and Great Expectations on the warehouse."),
    View("pipeline", pipeline_view, 1280, 800, "the daily run · sources to readers", "From the sources to the gate",
         "every figure passes the gate before anyone reads it",
         "EventZilla data platform — the daily run",
         "Pipeline diagram: the workbook and the scraped web pages land in an S3 bucket; Airbyte loads 55,260 rows "
         "into the raw schema; dbt builds the staging, quarantine, star and reporting tables with 43 tests; Great "
         "Expectations checks the star schema (15 of 15); only then do the app, the analyst, Metabase and n8n read "
         "the figures."),
    View("star", star_view, 1280, 900, "kimball star · marts schema", "The star schema",
         "one fact at the grain of a reservation, six dimensions",
         "EventZilla data platform — the star schema",
         "Star schema diagram: fact_reservation (18,000 rows, one per reservation) in the centre, with keys to six "
         "dimensions: dim_date (role-played by the reservation date and the event date), dim_event, dim_beneficiary "
         "on the left; dim_service, dim_provider and dim_geography on the right."),
]

if __name__ == "__main__":
    build(HERE, "EventZilla", VIEWS)
