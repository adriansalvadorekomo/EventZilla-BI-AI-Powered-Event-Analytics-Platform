# Key results

Every number below was measured on this repository's own runs (November 2026) and can be reproduced with the
command next to it. They are the only figures to quote about the project; nothing here is an estimate. The data is
synthetic (the team's original warehouse was lost), so the business findings describe the dataset, not a company.

## The rebuild in one paragraph

EventZilla v1 (2024, a team project) loaded an event-services workbook into a Talend warehouse; its fact table kept
**428 of 18,000** reservations. v2 rebuilds the platform end to end, under one rule: no figure reaches a reader
before it has passed a quality gate. Source files and scraped reference data land in an S3 bucket, Airbyte loads
them, dbt builds one star schema with 43 tests, Great Expectations gates the result, Airflow runs it every morning,
and Metabase, an API and an analysis app read it, the app with an analyst assistant that only runs read-only,
guarded SQL.

## Engineering results

| Result | Value | Reproduce |
|---|---|---|
| Reservations kept in the fact table | **18,000 of 18,000** (v1: 428) | `mise run quality` (row-count expectation) |
| Rows loaded by Airbyte per sync | **55,260**, exactly the source; 33–35 s per sync | Airbyte connection timeline, `docs/evidence/airbyte-*.png` |
| Daily pipeline, end to end | about **60 s** (land and scrape, Airbyte, dbt, two checkpoints); 3 consecutive green runs | Airflow, `docs/evidence/airflow-*.png` |
| dbt | **79 nodes pass**: 36 models, 43 tests (9 unique, 17 not null, 11 relationships, 3 accepted values, 3 singular) | `mise run build` |
| Quality gate on the star schema | **15 of 15** Great Expectations checks, logged to `quality.gate_runs` | `mise run quality` |
| Defects caught and isolated | 312 ratings outside 1–5, 12 non-existent months, 8,967 reservations dated after their event, 6 days with more bookings than visitors | `/api/quality`, data-quality page |
| Enrichment scraped with Firecrawl | 24 governorates with 2024 population and area, 60 public holidays 2022–2025; computed Islamic dates match Wikipedia on 7 of 8, the 8th by one day | `mise run scrape`, `docs/DATA_MODEL.md` |
| Dashboards as code | **5 Metabase dashboards, 28 cards**, one per business objective plus data quality | `mise run dashboards` |
| API | **38 tests** (SQL guard, assistant paths, endpoints on the live warehouse) | `mise run test:api` |
| Assistant safety | prompt injection blocked before any SQL (Prompt Guard score 0.9995 on the test attack); generated SQL parsed and refused unless it is one SELECT on the reporting schemas; runs as a read-only role with a 5 s limit; 12 attack patterns refused in tests | `backend/tests/` |
| Security and lint | **Bandit: 0 findings** at every severity; ruff clean | `mise run security`, `mise run lint` |
| Frontend | Angular 22, six pages lazy-loaded, **118 kB** initial transfer; design detector clean | `mise run build:web` |

## Data-science results (each judged by a gate set before training)

| Objective | Result | Decision |
|---|---|---|
| DSO1 revenue forecast (BO1) | All five models pass the team gate (SMAPE < 30 %, MASE < 1) on the 2025 holdout. The historical mean (SMAPE 15.73 %, MASE 0.72) is published over SARIMA (15.58 %) because it is simpler and only 0.15 points worse. | Forecast shown, labelled with its error |
| DSO2 confirmation prediction (BO2) | Gradient boosting, 5-fold AUC **0.499** against 0.505 for chance | **Stopped at the gate**: no prediction is served |
| DSO3 customer segments (BO3, BO4) | K-Means, silhouette 0.32 (gate 0.25): Active customers 73 %, Not yet converted 27 % (1,114 customers) | Segments shown; the second group is the follow-up target |

Reports: `ml/reports/*.json` (`mise run ml`).

## Business findings on the dataset

- Confirmed revenue 14.7–15.4 million a year; **+4.4 %** in 2025 against 2024. Weddings bring 26.7 %.
- About a third of reservations end confirmed, pending and cancelled, in every quarter.
- Ramadan days bring 11 % less revenue than other days, public holidays 10 % less: **both could be chance**
  (p = 0.10 and 0.15).
- Average rating 2.99 / 5; 34.5 % of evaluated reservations rated 4 or more; 75.7 % of customers come back.
- Spend per new customer: 9.2 in cheap months, 14.5 in normal months, 42.0 in expensive months; spend does not
  move revenue (rank correlation −0.19, p = 0.37).
- Revenue does not follow population across governorates (correlation −0.01): per-inhabitant rankings mostly
  reward small governorates.

## Statements to adapt

Draft wording for the CV, LinkedIn and the portfolio. Each sentence uses only the figures above; keep the honest
frame ("rebuilt", "synthetic data", "team project v1").

**PAR (Problem, Action, Result)**
- *Problem:* the team warehouse behind our event-analytics project was lost, and v1's fact table kept 428 of 18,000
  reservations. *Action:* rebuilt the platform with Airbyte, dbt, Great Expectations and Airflow, with one star
  schema and a quality gate before any report. *Result:* 18,000 of 18,000 reservations kept, 79 dbt nodes and 15
  gate checks passing, a 60-second daily run.

**STARL (Situation, Task, Action, Result, Learning)**
- *Situation:* a v1 BI project whose warehouse was gone and whose numbers could not be trusted.
- *Task:* rebuild it so that every figure is checked before anyone reads it.
- *Action:* S3 landing plus Firecrawl enrichment, Airbyte loads, a dbt star schema with 43 tests, a Great
  Expectations gate, Airflow orchestration, Metabase dashboards as code, and an Angular app with a guarded analyst
  assistant (read-only SQL, prompt-injection screening).
- *Result:* 18,000 of 18,000 reservations, 4 data defects isolated and counted, 5 dashboards, Bandit at 0
  findings.
- *Learning:* a model that cannot beat chance (AUC 0.50) is a result: the app says so instead of showing a
  prediction.

**CARL (Context, Action, Result, Learning)**
- *Context:* event-services analytics on a lost warehouse, rebuilt on synthetic data.
- *Action:* designed the star schema around the business objectives (GIMSI) and gated every load.
- *Result:* figures with their freshness and gate status on every screen ("rebuilt at, 15 of 15 checks").
- *Learning:* the simplest forecast that passes the gate beats a marginally better complex one.
