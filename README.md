# EventZilla — event analytics on a gated data platform

An event-services marketplace's data, loaded every morning into **one star schema that is tested and checked
before anyone reads it**, then read by managers in an analysis app and Metabase, with an analyst that answers
questions from the warehouse, in plain words and without ever exposing the query behind the answer.

> **v1 (Feb–May 2026)** was an ESPRIT team project of six, built together with my teammates, among them
> [walid0202](https://github.com/walid0202), [Karim Makni](https://github.com/karimmakni0) and
> [Hejer Mnejja](https://github.com/hejermnejja), whose commits are in this repository's history. The team built
> the Talend ETL, the Power BI dashboards and a first SQL assistant; my part was integration, Docker/nginx delivery
> and chatbot/API fixes. That warehouse was later lost.
> **v2 (November 2026)** is a rebuild I did alone, from the same source structure. The data is **synthetic**: the
> method and the checks are real, the figures are not company results. v1 is kept in tag
> [`v1-talend`](../../tree/v1-talend).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/c4/c4-container-dark.svg">
  <img src="docs/diagrams/c4/c4-container-light.svg" width="100%" alt="C4 container diagram of EventZilla. Managers open the Angular analysis app, which calls the FastAPI service; the API asks Groq to screen questions and write SQL, and reads the PostgreSQL warehouse through a read-only role. Metabase reads the warehouse. Prometheus scrapes the API and Grafana reads Prometheus; n8n calls the API. Airflow lands files in a SeaweedFS S3 bucket, scrapes Firecrawl monthly and triggers Airbyte, which reads the bucket and loads the raw schema; Airflow then runs dbt and Great Expectations on the warehouse.">
</picture>

## In short

EventZilla started as a team project: with my teammates, v1 loaded an Excel workbook through Talend into a
warehouse whose fact table kept **428 of 18,000** reservations, and nothing said so. Then the warehouse was lost.

I rebuilt it alone as v2, so that every figure is checked before a manager reads it, and so that what was left out, and why, is
said plainly. The workbook and two public reference tables scraped with Firecrawl land in an S3 bucket; Airbyte
loads them into PostgreSQL, dbt builds one Kimball star with 43 tests, Great Expectations gates the result and
Airflow runs it all at 05:00. Managers read the business objectives (GIMSI) in Metabase and in an Angular app whose
analyst runs only guarded, read-only SQL.

All **18,000 of 18,000** reservations are kept, **79 dbt nodes** and **15 of 15** gate checks pass, and **4 kinds
of source defect** are isolated and counted, not hidden. The daily run takes about **60 s**, and Bandit reports
**0** findings.

A model that predicts no better than chance (AUC 0.50) is a result too: the app says so instead of showing a
prediction, and the simplest forecast that passes its gate is the one published.

All figures, with the command that reproduces each: [docs/KEY_RESULTS.md](docs/KEY_RESULTS.md).

## What it does

| | |
|---|---|
| **Load** | The source workbook (16 sheets) and two scraped tables (24 governorates with 2024 population, 60 public holidays) land in a SeaweedFS S3 bucket; Airbyte loads the 18 streams into `raw`, 55,260 rows, exactly the source. |
| **Model** | dbt builds typed staging tables, a quarantine for rows that fail a rule, one star schema (`fact_reservation` + 6 dimensions) and reporting tables at other grains. 36 models, 43 tests. |
| **Gate** | Great Expectations checks the star: no reservation lost, unique keys, valid statuses, ratings within 1–5, no personal data in the customer table. Each result is logged in `quality.gate_runs`. |
| **Read** | Metabase: 5 dashboards as code, one per business objective plus data quality. The analysis app: a board of the four objectives, one page per objective and data quality. |
| **Ask** | The analyst turns a question into one SELECT, checks it, runs it read-only and answers from the rows it got. `/questions` lists the questions worth asking, with today's answer and the decision each informs. |
| **Automate** | n8n: an hourly freshness watch ("figures must not be presented" when stale or gated), a weekly decision brief, a webhook to ask the analyst. |
| **Watch** | Prometheus and Grafana on the API and the analyst: traffic, speed, errors, how each question ended; four alert rules. |

## The analysis app

The board shows the four business objectives as market tiles, each with its figure, change and trend. Below them,
a strip says what the quality rules caught, when the figures were rebuilt and whether they passed the gate.

![The board: revenue, reservations, customers and marketing as market tiles; the strip says the figures passed the gate, 15 of 15 checks](docs/evidence/app-board.png)

| The analyst answers in plain words | `/questions`: today's answer and the decision it informs |
|---|---|
| ![The analyst answering which event type brings the most revenue, with its steps, the answer and a ranked bar chart](docs/evidence/app-analyst-answer.png) | ![The /questions command listing the questions worth asking per objective with their current values](docs/evidence/app-analyst-questions.png) |
| **An injection attempt stops at the gate** | **Phone** |
| ![A prompt-injection attempt stopped at the gate before any query](docs/evidence/app-analyst-gate.png) | ![The board on a phone](docs/evidence/app-mobile.png) |

- **Charts:** prediction-market style. A crosshair scrubs every series, the readout follows it, and the arrow
  keys scrub too; each chart has a table for screen readers. Value axes start at zero (ratings at the bottom of
  their 1–5 scale), because on flat synthetic data a cropped axis would turn noise into drama.
- **Plain words first:** p-values and correlations sit behind "how this is computed" popovers. Changes under 5 %
  are called small.
- **Ctrl/⌘ K:** jumps to any page, runs a suggested question or asks anything.
- **Design:** recorded in [DESIGN.md](DESIGN.md), the product in [PRODUCT.md](PRODUCT.md).

**How the analyst stays safe** ([backend/app/assistant.py](backend/app/assistant.py)):
1. Llama Prompt Guard 2 screens the question (an injection scored 0.9995 is stopped before any SQL).
2. gpt-oss-120b writes one SELECT from a semantic layer of the warehouse.
3. sqlglot refuses anything but one SELECT on the reporting schemas, refuses dangerous functions and caps the
   rows at 200.
4. The query runs as `analyst_ro`, which is read-only, times out after 5 s and cannot see the raw tables
   (personal data).
5. A failing query is repaired once and checked again; the answer is written from the rows actually returned.

## Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/c4/c4-pipeline-dark.svg">
  <img src="docs/diagrams/c4/c4-pipeline-light.svg" width="100%" alt="The daily run: the workbook and the scraped pages land in an S3 bucket; Airbyte loads 55,260 rows into the raw schema; dbt builds the staging, quarantine, star and reporting tables with 43 tests; Great Expectations checks the star (15 of 15); only then do the app, the analyst, Metabase and n8n read the figures.">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/c4/c4-star-dark.svg">
  <img src="docs/diagrams/c4/c4-star-light.svg" width="100%" alt="The star schema: fact_reservation in the centre, one row per reservation, with keys to dim_date (role-played by the reservation and event dates), dim_event and dim_beneficiary on the left, and dim_service, dim_provider and dim_geography on the right.">
</picture>

| Container | Technology | Responsibility |
|---|---|---|
| Landing bucket | SeaweedFS (S3 API) | The workbook's CSVs and the scraped pages, as received |
| Extract and load | Airbyte 2.5 (abctl) | S3 source → PostgreSQL `raw`, 18 streams |
| Warehouse | PostgreSQL 16 | `raw` → `staging` → `marts` (the star), `reporting`, `reference`, `quality`; one database per tool on the same server |
| Transform and test | dbt 1.10 | 36 models, 43 tests, lineage ([docs/DATA_MODEL.md](docs/DATA_MODEL.md)) |
| Gate | Great Expectations 1.25 | `raw` checkpoint (reports source defects), `star_schema` checkpoint (gates) |
| Orchestration | Airflow 2.10 | `eventzilla_daily` at 05:00: land and scrape, sync, build, check |
| Dashboards | Metabase 0.65 | 5 dashboards built by `analytics/metabase/setup_dashboards.py` |
| API | FastAPI | Indicators, `/api/questions`, the analyst `/api/ask`, `/api/status`, `/metrics` |
| Analysis app | Angular 22, GSAP, nginx | Board, objective pages, the analyst, ⌘K palette |
| Automation | n8n 2.50 | Freshness watch, weekly decision brief, ask webhook ([automation/n8n](automation/n8n)) |
| Monitoring | Prometheus 3.16, Grafana 13.2 | API and analyst dashboard, 4 alert rules |

The business objectives (BO1 revenue, BO2 reservations, BO3 satisfaction, BO4 marketing), the data-science
objectives and the indicator catalogue follow the GIMSI method: [docs/GIMSI.md](docs/GIMSI.md). The star schema,
its tests, the lineage, the Firecrawl enrichment and the model's limits: [docs/DATA_MODEL.md](docs/DATA_MODEL.md).

## Data quality

| Rule | Rows | What happens |
|---|---|---|
| Evaluation rating outside 1–5 | 312 of 12,000 | quarantined, left out of every average |
| Marketing row that is not a calendar month | 12 of 36 | quarantined |
| Reservation dated after its own event | 8,967 of 18,000 | kept (its revenue is real), flagged; no lead-time indicator anywhere |
| Website day with more bookings than visitors | 6 of 365 | kept, flagged, conversion left empty |

## Data science, each judged by a gate set before training

| Objective | Result | Decision |
|---|---|---|
| Revenue forecast (BO1) | All five models pass SMAPE < 30 % and MASE < 1 on 2025; the historical mean (15.73 %) is published over SARIMA (15.58 %) because it is simpler | shown, with its error |
| Confirmation prediction (BO2) | AUC 0.499 against 0.505 for chance | **stopped at the gate**, not served |
| Customer segments (BO3, BO4) | silhouette 0.32 (gate 0.25): 73 % active, 27 % booked but never confirmed | shown; the second group is the follow-up target |

## Evidence

All screenshots come from real runs on this stack ([docs/evidence](docs/evidence)).

| Airflow: the daily DAG | Airflow: task durations |
|---|---|
| ![Airflow graph of eventzilla_daily](docs/evidence/airflow-dag-graph.png) | ![Airflow task durations over the runs](docs/evidence/airflow-task-duration.png) |
| **Airbyte: sync timeline** | **dbt: lineage of the fact** |
| ![Airbyte connection timeline](docs/evidence/airbyte-sync-timeline.png) | ![dbt lineage of fact_reservation](docs/evidence/dbt-lineage-fact-reservation.png) |
| **Metabase: revenue** | **Grafana: API and analyst** |
| ![Metabase revenue dashboard](docs/evidence/metabase-1-revenue.png) | ![Grafana dashboard after real traffic](docs/evidence/grafana-api-and-analyst.png) |
| **Great Expectations: the raw checkpoint** | **n8n: the decision brief's run** |
| ![Great Expectations finding 312 ratings outside 1-5](docs/evidence/great-expectations-raw-ratings.png) | ![n8n execution of the weekly decision brief](docs/evidence/n8n-decision-brief-run.png) |

## Quick start

Needs Docker, [mise](https://mise.jdx.dev) and [abctl](https://docs.airbyte.com/platform/using-airbyte/getting-started/oss-quickstart) for Airbyte.

```sh
mise run setup            # .env from the example: set the passwords and keys, then run it again
mise run up               # warehouse, landing, Airflow, Metabase, n8n, API, app, monitoring
mise run airbyte:install  # Airbyte beside the stack, port 8006, its own HOME
mise run airbyte:setup    # source, destination and connection
mise run trigger          # the daily DAG now; or step by step: mise run pipeline
mise run dashboards       # the Metabase dashboards (needs an admin API key)
mise run n8n:import       # the n8n workflows
```

Then open the app on <http://localhost:4200>, Metabase on :3001, Airflow on :8080, Grafana on :3000 and n8n on
:5678. Every port is bound to 127.0.0.1.

### Images on Docker Hub

Built from this branch and scanned for secret files before publishing; `compose.yaml` uses them.

| Image | Contents |
|---|---|
| [`twelvy1400/eventzilla-api`](https://hub.docker.com/r/twelvy1400/eventzilla-api) | the API and the analyst, with the data-science reports; non-root, health check |
| [`twelvy1400/eventzilla-frontend`](https://hub.docker.com/r/twelvy1400/eventzilla-frontend) | the analysis app on nginx, `/api` proxied to the API |
| [`twelvy1400/eventzilla-airflow`](https://hub.docker.com/r/twelvy1400/eventzilla-airflow) | Airflow 2.10 with dbt and Great Expectations in their own virtual environments |

Tags: `:latest` and the short commit they were built from.

## Commands

`mise run help` lists all of them. The most useful:

| Command | What it does |
|---|---|
| `mise run pipeline` | land, scrape, sync, build, quality, from the host |
| `mise run build` | dbt: rebuild and test everything (79 nodes) |
| `mise run quality` | Great Expectations: raw checkpoint, then the star-schema gate |
| `mise run docs` | dbt docs with the lineage on :8081 |
| `mise run ml` | the three data-science objectives, rewriting `ml/reports/` |
| `mise run api` · `mise run web` | the API and the app in development |
| `mise run check` | lint (ruff), security (Bandit), API tests, frontend build |

## API

| Endpoint | Purpose |
|---|---|
| `GET /api/overview` | Headline indicators |
| `GET /api/revenue/monthly` · `/api/revenue/by/{event_type,service,region,governorate}` | Revenue over time and by group, with share and revenue per 1,000 inhabitants |
| `GET /api/reservations/status` · `/calendar` · `/api/conversion/weekly` | Outcomes per quarter, revenue per type of day, website conversion |
| `GET /api/customers` · `/api/marketing` · `/api/quality` | Ratings, complaints, marketing cost, quality rules |
| `GET /api/models` | The data-science reports with their gates |
| `GET /api/questions` | The questions worth asking: today's answer and the decision each informs |
| `POST /api/ask` | The analyst: answer, the SQL that ran, the rows, a chart suggestion |
| `GET /api/status` | When the figures were rebuilt and the last gate result |
| `GET /health` · `GET /metrics` | Liveness · Prometheus |

## Layout

```
ingestion/        land the workbook, scrape the enrichment, set up Airbyte
transformation/   dbt project: staging, quality, marts (the star), reporting, reference
quality/          Great Expectations checkpoints
orchestration/    Airflow image and the daily DAG
analytics/        the EDA notebook and the Metabase dashboards as code
ml/               the data-science objectives and their reports
backend/          the API and the analyst
frontend/         the analysis app
automation/n8n/   the n8n workflows
monitoring/       Prometheus rules and the Grafana dashboard
infra/            warehouse init (databases, schemas, the read-only role)
docs/             data model, GIMSI, key results, diagrams, evidence
```

## Limits and next steps

These are the limits a senior review raised; details and fixes are in
[docs/DATA_MODEL.md](docs/DATA_MODEL.md#limits-of-the-model-and-what-would-fix-them).

- **Keys:** natural keys, no surrogate keys or history (SCD2). Next: surrogate keys, a −1 "unknown" member in
  every dimension, and dbt snapshots.
- **Integrity:** tested rather than built in. The fact is built from staging rather than from the dimensions,
  and `governorate_id` is derived in two places. Next: build the fact from the dimensions and keep the
  governorate on `dim_provider` only.
- **Data:** synthetic and statistically independent across columns, so most differences between groups are
  small; the app says so rather than ranking noise.
- **Airbyte:** runs beside the stack (abctl), not inside it; the sync is a full refresh of a small source.
