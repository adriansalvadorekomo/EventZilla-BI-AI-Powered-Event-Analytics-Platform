# GIMSI: from business objectives to indicators

EventZilla is analysed with the GIMSI method (Alain Fernandez): start from the decisions people take, derive the
objectives, then the indicators that serve them, and only then the data and the tools. This page records each
step for the rebuilt platform. The star schema ([DATA_MODEL.md](DATA_MODEL.md)) and every dashboard follow from
it; the verified figures are in [KEY_RESULTS.md](KEY_RESULTS.md).

The data is synthetic (the team's original warehouse was lost). The method and the indicators are real; today's
values describe the dataset, not a company.

## The company and its decision-makers (steps 1–2: environment, activities)

EventZilla is a Tunisian marketplace for event services. Customers ("beneficiaries") plan weddings, corporate
events, birthdays and private parties; independent providers sell venues, catering, entertainment and
decoration; EventZilla takes the reservation, the follow-up and the complaints. Activity covers 2022–2025 and the
country's 24 governorates.

| Decision-maker (role) | Decisions they take | Objective |
|---|---|---|
| General manager | budget, growth, where to expand | BO1 |
| Sales and operations manager | follow-up of pending bookings, staffing over the year | BO2 |
| Customer-relations manager | service quality, loyalty offers, provider reviews | BO3 |
| Marketing manager | campaign spend and its level | BO4 |
| Data team | whether the figures can be trusted | all (data quality) |

The roles are those of a company of this kind; no person or real organisation is implied.

## Business objectives (step 3)

| | Objective | The question it answers |
|---|---|---|
| **BO1** | Revenue and profitability | Is the business making money, and where does it come from? |
| **BO2** | Reservations and conversion | How many bookings turn into business, and what changes it? |
| **BO3** | Satisfaction and retention | Are customers satisfied, and do they come back? |
| **BO4** | Marketing return | Does marketing spend bring customers and revenue? |

## Data-science objectives (derived from the business ones)

Each has a gate set before training; a model that misses it is not shown.

| | Objective | Serves | Gate | Result |
|---|---|---|---|---|
| **DSO1** | Forecast monthly confirmed revenue, six months ahead | BO1 | SMAPE < 30 %, MASE < 1 on a 12-month holdout | passed (historical mean, SMAPE 15.73 %) |
| **DSO2** | Predict whether a reservation will be confirmed | BO2 | ROC AUC ≥ 0.60 and above chance | **failed** (AUC 0.499): not served |
| **DSO3** | Segment customers by behaviour | BO3, BO4 | silhouette ≥ 0.25 | passed (0.32): 73 % active, 27 % not yet converted |

Code and reports: `ml/` and `ml/reports/*.json`.

## Indicators (steps 4–5: dashboard design, choice of indicators)

Every indicator below is computed in the warehouse with one definition, shared by Metabase, the API and the app.
A target is a management decision: none was set for this dataset, so the column says **open** rather than invent
one. The only target the original project stated is a "+15 % reservation rate"; the 2022 website conversion
(median day 5.4 %) is the baseline it would be measured against.

| Objective | Indicator | Definition | Today | Target |
|---|---|---|---|---|
| BO1 | Confirmed revenue | sum of the agreed price of confirmed reservations | 15.35 million in 2025 | open |
| BO1 | Revenue growth | year against the year before | +4.4 % (2025) | open |
| BO1 | Revenue by event type, service, region, governorate | share of confirmed revenue | weddings 26.7 % | open |
| BO1 | Revenue per 1,000 inhabitants | regional revenue over regional population (2024) | South West 10,679; read with care, see DATA_MODEL | open |
| BO1 | Revenue forecast | DSO1, six months | about 7.4 million for Jan–Jun 2026 | n/a |
| BO2 | Confirmation share | confirmed over all reservations | 33.5 % (last 4 quarters 32.6 %) | open |
| BO2 | Pending and cancelled shares | same, per status | 33.2 % and 33.3 % | open |
| BO2 | Revenue per day by type of day | Ramadan, public holiday, other days | −11 % and −10 % against other days; could be chance | n/a |
| BO2 | Website conversion | daily bookings over daily visitors, valid days, 2022 | median day 5.4 % | +15 % (original project) |
| BO3 | Average rating | mean of valid 1–5 evaluations | 2.99 / 5 | open |
| BO3 | Rated 4 or more | share of evaluated reservations | 34.5 % | open |
| BO3 | Returning customers | customers with more than one event | 75.7 % | open |
| BO3 | Complaints per 100 reservations | by region | 13.2 to 15.5 (small spread) | open |
| BO4 | Spend per new customer | total spend over new customers, pooled | 22.4 overall; cheap months 9.2, expensive 42.0 | open |
| BO4 | Spend against revenue | rank correlation over the valid months | −0.19, no link | n/a |
| Quality | Rows left out or flagged | per quality rule | 312 ratings, 12 months, 8,967 dates, 6 days | 0 new defects |
| Quality | Gate | Great Expectations checks on the star schema | 15 of 15 | 15 of 15 |

## Data collection (step 6)

| Source | What it gives | How it arrives |
|---|---|---|
| Source workbook (16 sheets) | reservations, events, services, providers, customers, evaluations, complaints, marketing, traffic, competitors | split to CSV, landed in S3, loaded by Airbyte |
| Wikipedia, scraped with Firecrawl | 24 governorates (population 2024, area), public holidays 2022–2025 | landed in S3 next to the workbook; Islamic dates cross-checked |

## The system of dashboards (step 7)

- Metabase: one dashboard per objective plus data quality, built as code (`analytics/metabase/`).
- The analysis app (`frontend/`): the board shows the four objectives as market tiles. Each objective has a page
  with its questions to decide on, and an analyst answers further questions from the warehouse.
- The board's strip and the data-quality page carry the gate result and the time of the last rebuild.

## Tools (step 8)

| Layer | Tool | Why |
|---|---|---|
| Landing | SeaweedFS (S3 API) | a bucket that runs locally and speaks S3 |
| Extract and load | Airbyte | declared connections, schema discovery, sync history |
| Transform and test | dbt | the star schema as code, with tests and lineage |
| Data quality gate | Great Expectations | checks on the final tables, results kept |
| Orchestration | Airflow | one daily DAG, retries, durations |
| Dashboards | Metabase | managers' self-service, dashboards as code |
| Application | FastAPI, Angular, Groq | the analyst and the objective pages |

## Integration and audit (steps 9–10)

- Airflow runs the chain every morning at 05:00 (`eventzilla_daily`): land and scrape, Airbyte, dbt, then the two
  checkpoints. A failing dbt test stops the tables that depend on it; a failing gate marks the run failed.
- Auditing is continuous. Every gate result is logged in `quality.gate_runs`. Each rule's counts are on the
  data-quality page. The model gates are rerun with `mise run ml`.
- The model's known limits and the next steps are in DATA_MODEL.md ("Limits of the model").
