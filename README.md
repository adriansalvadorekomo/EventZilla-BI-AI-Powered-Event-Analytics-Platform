# EventZilla BI — AI-Powered Event Analytics Platform

**End-to-end event analytics platform** — star-schema warehouse, ETL, ML forecasting/anomaly detection, NL-to-SQL, and containerized microservices.

> Academic team project (6 people). My scope: integration, Docker/nginx delivery, and chatbot/API fixes.

<p>
  <a href="https://deepwiki.com/adriansalvadorekomo/Esprit-PABI-4ERPBI6-2526-EventZella"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki" /></a>
</p>

<p>
  <sub>👋 Hi, I'm <a href="https://github.com/adriansalvadorekomo"><b>Adrian Salvador Ekomo</b></a> — Computer Engineering student building toward a <b>Junior Data Engineer</b> role. This repo is my proof of work.</sub>
</p>

<p>
  <sub>📖 Full wiki: <a href="https://deepwiki.com/adriansalvadorekomo/Esprit-PABI-4ERPBI6-2526-EventZella">deepwiki.com/adriansalvadorekomo/Esprit-PABI-4ERPBI6-2526-EventZella</a></sub>
</p>

---

## Contents

- [1. Project Overview](#1-project-overview)
- [2. Architecture](#2-architecture)
  - [Overall Architecture Diagram](#overall-architecture-diagram)
  - [Architecture Diagram Sources (D2 · Graphviz)](#architecture-diagram-sources-d2--graphviz)
  - [The 11 Microservices](#the-11-microservices)
  - [End-to-End Data Flow](#end-to-end-data-flow)
- [3. Data Platform — ETL & Warehouse](#3-data-platform--etl--warehouse)
- [4. Backend & AI Services](#4-backend--ai-services)
- [5. Machine Learning & MLOps](#5-machine-learning--mlops)
- [6. Frontend & BI](#6-frontend--bi)
- [7. Infrastructure & Observability](#7-infrastructure--observability)
- [8. Getting Started](#8-getting-started)
- [9. Tech Stack](#9-tech-stack)
- [10. Conclusion](#10-conclusion)

---

## 1. Project Overview

Event organizers drown in disconnected data — ticketing here, bookings there, marketing spend somewhere else. Nobody can answer "which events actually make money?" without a week of spreadsheet surgery.

EventZilla BI is our answer: an AI-powered analytics platform that unifies event, booking, and marketing data into one star-schema warehouse, forecasts demand, detects anomalies, and lets anyone ask questions in plain language. Six of us built it as an academic project; I owned the seams that hold a platform together — integration across services, Docker/nginx delivery, and the chatbot/API fixes that kept the natural-language interface reliable end to end.

- **Status:** Platform live via Docker Compose — warehouse, ML models, chatbot, dashboards, and monitoring all running.
- **Full wiki:** [deepwiki.com/adriansalvadorekomo/Esprit-PABI-4ERPBI6-2526-EventZella](https://deepwiki.com/adriansalvadorekomo/Esprit-PABI-4ERPBI6-2526-EventZella)

---

## 2. Architecture

### Overall Architecture Diagram

![EventZilla data-platform architecture](docs/architecture.svg)

*Source systems flow through Talend ETL and Airflow ingestion into a PostgreSQL
star-schema warehouse organized around business questions. MLflow-tracked models
serve a natural-language interface over 11 Dockerized microservices behind nginx.*

### Architecture Diagram Sources (D2 · Graphviz)

The diagrams are maintained as text — version-controlled, easy to update, with SVG committed for direct viewing.

- **D2 source** — [`docs/architecture.d2`](docs/architecture.d2), the preferred format for readability:
  `d2 docs/architecture.d2 docs/architecture.svg`
- **Graphviz (DOT) source** — [`docs/architecture.dot`](docs/architecture.dot), for broader compatibility:
  `dot -Tsvg docs/architecture.dot -o docs/architecture-gv.svg`

### The 11 Microservices

Traffic is routed by Nginx across 11 containerized services orchestrated with Docker Compose:

| Service | Role / Technology | Entry point |
|---|---|---|
| Nginx proxy | Reverse proxy & static assets | [`docker/nginx.conf`](docker/nginx.conf) |
| Angular frontend | Role-based SPA dashboard | [`eventzilla-front/`](eventzilla-front/) |
| FastAPI backend | REST API, ML inference, chatbot | [`backend/api/main.py`](backend/api/main.py) |
| Flask service | Legacy analytics & BI endpoints | [`backend/app.py`](backend/app.py) |
| PostgreSQL DW | Star-schema warehouse | [`scripts/dw_schema.sql`](scripts/dw_schema.sql) |
| Airflow | Ingestion orchestration | [`etl/airflow/AUTOMATIZATION`](etl/airflow/AUTOMATIZATION) |
| Talend ETL | Staging & warehouse transforms | [`etl/talend/`](etl/talend/) |
| MLflow | Experiment tracking & model registry | [`backend/train*.py`](backend/train_prophet.py) |
| Prometheus | Pipeline metrics scraper | [`docker/prometheus.yml`](docker/prometheus.yml) |
| Grafana | Operational & business dashboards | [`docker/grafana/`](docker/) |
| n8n | Automated retraining workflows | [`ml/n8n/`](ml/n8n/) |

### End-to-End Data Flow

- **Extraction** — Talend jobs (`job_master_sa`) ingest raw event, booking, and marketing data into staging
- **Orchestration** — Airflow (`AUTOMATIZATION`) schedules and orders the transformation pipelines
- **Warehousing** — data lands in a PostgreSQL star-schema (`Fact_Revenues` + 13 dimension tables: date, category, location, saison, beneficiary, provider, service, event, reservation, evaluation, complaint, competitor, reviews)
- **ML & MLOps** — training scripts extract warehouse features for Prophet forecasting, statsmodels anomaly detection, and scikit-learn classification, all tracked in MLflow
- **Serving** — FastAPI serves predictions and NL-to-SQL answers, Angular serves 4 role-based profiles, Power BI connects directly to the warehouse

---

## 3. Data Platform — ETL & Warehouse

- **Talend** — `job_master_sa` (source → staging) and `job_master_dw` (staging → warehouse) under [`etl/talend/`](etl/talend/)
- **Airflow** — dependency trees and schedules under [`etl/airflow/AUTOMATIZATION`](etl/airflow/AUTOMATIZATION)
- **Warehouse DDL** — [`scripts/dw_schema.sql`](scripts/dw_schema.sql): `Fact_Revenues` organized around business questions, not source schemas
- **Prep utilities** — [`scripts/`](scripts/) (staging SQL, imputers, verification)

---

## 4. Backend & AI Services

- **FastAPI** ([`backend/api/main.py`](backend/api/main.py)) — core REST API: predictions, metrics, and NL-to-SQL chatbot responses
- **Flask (legacy)** ([`backend/app.py`](backend/app.py)) — earlier analytics/BI endpoints, kept running behind the proxy
- **Chatbot backend** — natural-language-to-SQL over the warehouse (Groq LLaMA 3.3-70b), auto-rendering charts so anyone can explore the data

---

## 5. Machine Learning & MLOps

- **Forecasting** — Prophet for event demand seasonality (MAPE under 15%), plus LSTM/time-series experiments ([`backend/train_prophet.py`](backend/train_prophet.py), [`backend/train_ts.py`](backend/train_ts.py))
- **Anomaly & classification** — statsmodels detectors, scikit-learn classifiers, clustering (K-Means, DBSCAN)
- **Tracking** — MLflow experiment tracking, model registry, automated comparison ([`backend/compare_models.py`](backend/compare_models.py))
- **Retraining** — n8n automation workflows under [`ml/n8n/`](ml/n8n/); analysis notebooks under [`ml/notebooks/`](ml/notebooks/)

---

## 6. Frontend & BI

- **Angular SPA** ([`eventzilla-front/`](eventzilla-front/)) — 4 role-based profiles (marketing, quality, operations, business), shared header/footer/chart components, and an embedded chatbot widget
- **Power BI** ([`pbi-dashboard/`](pbi-dashboard/)) — deep-dive exploratory analysis straight from the warehouse

---

## 7. Infrastructure & Observability

- **Deployment** — [`docker-compose.yaml`](docker-compose.yaml): 11 microservices, multi-stage builds, Nginx reverse proxy, Cloudflare Tunnel
- **Monitoring** — Prometheus + Grafana: ML Pipeline Health, API Performance, Business KPIs, System Health, with custom PromQL alerts
- **Helpers** — `start.bat`, `start-backend.bat`, `start-tunnel.bat`; backend config via `backend/.env.example`

---

## 8. Getting Started

```bash
# Clone the repository
git clone https://github.com/adriansalvadorekomo/Esprit-PABI-4ERPBI6-2526-EventZella.git
cd Esprit-PABI-4ERPBI6-2526-EventZella

# Start all services
docker compose up -d

# Access the dashboard
open http://localhost:4200
```

---

## 9. Tech Stack

| Category | Technologies |
|---|---|
| Frontend | Angular 20, TypeScript |
| Backend | FastAPI, Flask (legacy), Python |
| Database | PostgreSQL (star-schema DW) |
| ETL/Orchestration | Talend, Airflow |
| ML | Prophet, statsmodels, scikit-learn, PyTorch, MLflow |
| BI | Power BI |
| Monitoring | Prometheus, Grafana |
| Automation | n8n |
| Infrastructure | Docker Compose, nginx, Cloudflare Tunnel |

---

## 10. Conclusion

EventZilla taught me the hardest part of data platforms isn't the models — it's the seams: getting eleven services to agree, keeping a chatbot honest against a real warehouse, and delivering it all in one `docker compose up`. I owned those seams, and I'd do it again.

If you need someone who thinks in systems and ships integrations that hold, let's talk.

---

<p align="center">
  <sub>Academic team project · My scope: integration, Docker/nginx delivery, chatbot/API fixes</sub>
  <br />
  <sub>👋 <a href="https://github.com/adriansalvadorekomo"><b>Adrian Salvador Ekomo</b></a> · <a href="https://linkedin.com/in/adrian-salvador-ekomo-mesi-obono-5990b8182">LinkedIn</a> · seeking a Junior Data Engineer role</sub>
</p>
