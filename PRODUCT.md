# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The managers of EventZilla, a Tunisian event-services marketplace (weddings, corporate events, birthdays, private parties; venues, catering, entertainment, decoration from independent providers). They are not technical. They open the app to answer one business question at a time (are we making money and where, do bookings turn into business, are customers satisfied and coming back, does marketing pay) and to decide what to do next. Confirmed with the owner on 2026-11-24.

Second audience: recruiters and hiring engineers who open the project from the owner's portfolio, GitHub or LinkedIn. For them the app must read as a believable product, and the repository carries the engineering proof.

## Product Purpose

The analysis front of the EventZilla data platform. It turns the star schema (one fact, six dimensions, rebuilt with Airbyte, dbt, Great Expectations and Airflow) into answers a manager can act on, organised by the four business objectives of the GIMSI study, plus a data-quality page and an analyst assistant that answers questions in plain language from the warehouse. It succeeds when a manager understands, in one screen per objective, what happened, how big it is, and how far to trust it.

## Positioning

Every figure is checked before it is shown: the warehouse passes 78 dbt nodes and a Great Expectations gate, rows that fail a rule are quarantined and counted on the data-quality page, and the assistant only answers with SQL it has guarded and run read-only, showing the rows it used. The app says plainly when a difference is small or not significant, and when a model did not pass its gate.

## Operating Context

- Managers read it on a laptop in a meeting or before one; it must also hold on a phone.
- The data is synthetic (the team's original warehouse was lost) and covers 2022-2025: 18,000 reservations, 24 governorates. Columns are statistically independent, so most group differences are small; the app must not dramatise them.
- The figures match the Metabase dashboards (same definitions, same warehouse).

## Capabilities and Constraints

- Angular 22 (standalone components, signals, zoneless), GSAP for motion; served by nginx, API at `/api` (FastAPI, `backend/`). Stack confirmed by the owner: keep Angular, rebuilt from scratch (on Angular 22: the 20 CLI predates the Node in use).
- English only (confirmed).
- API: `/api/overview`, `/api/revenue/monthly`, `/api/revenue/by/{event_type|service|region|governorate}`, `/api/reservations/status`, `/api/reservations/calendar`, `/api/conversion/weekly`, `/api/customers`, `/api/marketing`, `/api/quality`, `/api/models`, `POST /api/ask`.
- The assistant needs a Groq key; it can be busy (rate limit) or decline questions the data cannot answer. Both states are normal and must read as such.
- Amounts have no documented currency: never show a currency symbol.
- Measures with known defects are not charted: lead time (half the reservations are dated after their event).

## Brand Commitments

- The owner's identity (`~/Projects/portfolio-webapp/DESIGN.md`) is binding as an influence: IBM Plex Mono and Schibsted Grotesk, graphite grounds, one orange signal (#ff4f00) reserved for the gate and the primary action, an always-dark display, evidence over adjectives.
- The owner asked for an enterprise identity, analysis-oriented, with prediction-market style charts (Kalshi / Polymarket) and an advanced analyst assistant with GSAP motion.
- Stakeholder language: no technical words in the interface (no "fact", "dimension", "SQL" unless the user opens the assistant's working).
- A visible but quiet notice that the data is synthetic, on every page (confirmed).

## Evidence on Hand

- Every number comes from the API on the live warehouse; the verified figures are in `docs/DATA_MODEL.md`, `analytics/eda.ipynb` and `ml/reports/*.json`.
- Data-science results: revenue forecast passes its gate (historical mean published, SMAPE 15.7 %); confirmation prediction has no signal (AUC 0.499) and is not served; two customer segments (73 % active, 27 % not yet converted).
- No real customers, testimonials, logos or company claims exist; none may be invented.

## Product Principles

1. One business question per page, answered in the first screen.
2. Every figure carries its trust: definition, period, and the quality rule that touched it.
3. Say when a difference is small; never dramatise synthetic noise.
4. The assistant shows its work on request: the question, the query, the rows.
5. Same numbers everywhere: app, Metabase, documentation.

## Accessibility & Inclusion

WCAG AA contrast in every state; full keyboard path including the assistant; `prefers-reduced-motion` removes the assistant's staged motion and chart draw-ins; charts have text equivalents (headline figure and a table on demand).
