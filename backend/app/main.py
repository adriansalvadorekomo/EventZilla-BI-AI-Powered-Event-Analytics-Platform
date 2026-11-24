"""EventZilla analytics API.

    uvicorn app.main:app --port 8000

/api/overview ... /api/quality   the indicators of the four business objectives (same definitions as Metabase)
/api/models                      the data-science objectives, from ml/reports (measured, with their gates)
/api/ask                         the analyst assistant (needs GROQ_API_KEY)
/health, /metrics                for Docker and Prometheus
"""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from . import assistant, questions
from .db import records, run_readonly

REPORTS = Path(os.environ.get("REPORTS_DIR", Path(__file__).resolve().parents[2] / "ml" / "reports"))

app = FastAPI(title="EventZilla analytics API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:4200").split(","),
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
Instrumentator().instrument(app).expose(app, include_in_schema=False)

REGION_POP = "(select region, sum(population_2024) as pop from marts.dim_geography group by 1)"


@app.get("/health")
def health() -> dict:
    run_readonly("select 1")
    return {"status": "ok"}


@app.get("/api/overview")
def overview() -> dict:
    row = records("""
        select sum(revenue) as revenue, count(*) as reservations,
               round(100.0 * avg(is_confirmed::int), 1) as confirmation_rate,
               round(avg(rating_avg), 2) as average_rating,
               round(100.0 * (sum(revenue) filter (where reservation_date >= '2025-01-01'))
                 / nullif(sum(revenue) filter (where reservation_date between '2024-01-01' and '2024-12-31'), 0)
                 - 100, 1) as growth_2025_vs_2024
        from marts.fact_reservation""")[0]
    row.update(records("""select round(100.0 * avg(is_returning::int), 1) as returning_customers
                          from marts.dim_beneficiary where events > 0""")[0])
    row.update(records("""select sum(complaints) as open_complaints from reporting.rpt_complaint_summary
                          where status = 'open'""")[0])
    return row


@app.get("/api/revenue/monthly")
def revenue_monthly() -> list[dict]:
    return records("""select to_char(date_trunc('month', reservation_date), 'YYYY-MM') as month,
                             sum(revenue) as revenue, count(*) filter (where is_confirmed) as confirmed
                      from marts.fact_reservation group by 1 order by 1""")


GEO = "join marts.dim_geography g using (governorate_id)"
# label, join, population expression (None: no per-inhabitant figure). Whitelisted: never built from the request.
BREAKDOWNS = {
    "event_type": ("e.event_type", "join marts.dim_event e using (event_id)", None),
    "service": ("s.service_category", "join marts.dim_service s using (service_id)", None),
    "region": ("g.region", f"{GEO} join {REGION_POP} r on r.region = g.region", "max(r.pop)"),
    "governorate": ("g.governorate", GEO, "max(g.population_2024)"),
}


@app.get("/api/revenue/by/{dimension}")
def revenue_by(dimension: str) -> list[dict]:
    """Revenue, reservations and share of revenue per group; per 1,000 inhabitants for geographic groups.

    Read the per-inhabitant figure with care: across governorates revenue does not follow population
    (correlation -0.01), so it mostly ranks places by how few people live there.
    """
    if dimension not in BREAKDOWNS:
        raise HTTPException(404, f"unknown dimension; use one of {sorted(BREAKDOWNS)}")
    column, join, pop = BREAKDOWNS[dimension]
    region = ", max(g.region) as region" if dimension == "governorate" else ""
    per_capita = f", round(sum(f.revenue) * 1000.0 / {pop}) as revenue_per_1000_inhabitants" if pop else ""
    sql = (f"select {column} as label{region}, sum(f.revenue) as revenue, count(*) as reservations, "  # noqa: S608
           f"round(100.0 * sum(f.revenue) / sum(sum(f.revenue)) over (), 1) as share_pct{per_capita} "
           f"from marts.fact_reservation f {join} group by 1 order by sum(f.revenue) desc")  # nosec B608
    return records(sql)


@app.get("/api/reservations/status")
def reservation_status() -> list[dict]:
    return records("""select to_char(date_trunc('quarter', reservation_date), 'YYYY-"Q"Q') as quarter,
                             round(100.0 * avg(is_confirmed::int), 1) as confirmed,
                             round(100.0 * avg((status = 'pending')::int), 1) as pending,
                             round(100.0 * avg(is_cancelled::int), 1) as cancelled
                      from marts.fact_reservation group by 1 order by 1""")


@app.get("/api/reservations/calendar")
def reservation_calendar() -> list[dict]:
    return records("""
        with d as (select d.date_day, d.is_ramadan, d.is_holiday, coalesce(sum(f.revenue), 0) as revenue
                   from marts.dim_date d left join marts.fact_reservation f on f.reservation_date = d.date_day
                   group by 1, 2, 3)
        select case when is_ramadan then 'Ramadan' when is_holiday then 'Public holiday' else 'Other days' end
               as days, round(avg(revenue)) as revenue_per_day, count(*) as n_days
        from d group by 1 order by 2 desc""")


@app.get("/api/conversion/weekly")
def conversion_weekly() -> list[dict]:
    return records("""select to_char(date_trunc('week', traffic_date), 'YYYY-MM-DD') as week,
                             round(100.0 * (percentile_cont(0.5) within group (order by conversion_rate))::numeric, 2)
                               as conversion
                      from reporting.rpt_site_traffic_daily where is_valid group by 1 order by 1""")


@app.get("/api/customers")
def customers() -> dict:
    return {
        "rating": records("""select round(avg(rating_avg), 2) as average,
                                    round(100.0 * avg((rating_avg >= 4)::int), 1) as rated_4_or_more,
                                    round(100.0 * avg((rating_avg is not null)::int), 1) as evaluated
                             from marts.fact_reservation""")[0],
        "by_service": records("""select s.service_category as label, round(avg(f.rating_avg), 2) as rating
                                 from marts.fact_reservation f join marts.dim_service s using (service_id)
                                 where f.rating_avg is not null group by 1 order by 2 desc"""),
        "complaints_by_region": records("""
            select g.region as label, round(100.0 * sum(p.complaints) / max(r.n), 1) as per_100_reservations
            from marts.dim_provider p join marts.dim_geography g using (governorate_id)
            join (select g2.region, count(*) as n from marts.fact_reservation f
                  join marts.dim_geography g2 using (governorate_id) group by 1) r on r.region = g.region
            group by 1 order by 2 desc"""),
        "complaints_by_subject": records("""
            select subject as label, sum(complaints) filter (where status = 'open') as open,
                   sum(complaints) filter (where status = 'closed') as closed
            from reporting.rpt_complaint_summary group by 1 order by 2 desc"""),
    }


@app.get("/api/marketing")
def marketing() -> dict:
    return {
        "monthly": records("""select to_char(month_start, 'YYYY-MM') as month, marketing_spend, new_beneficiaries,
                                     confirmed_revenue from reporting.rpt_marketing_monthly order by 1"""),
        "by_type": records("""select spend_type as label,
                                     round(sum(marketing_spend) / nullif(sum(new_beneficiaries), 0), 1)
                                       as cost_per_new_customer
                              from reporting.rpt_marketing_monthly group by 1 order by 2"""),
    }


@app.get("/api/quality")
def quality() -> list[dict]:
    return records("""
        select 'Ratings outside the 1-5 scale' as rule, (select count(*) from quality.rejected_evaluations) as rows,
               12000 as of_rows, 'left out of every average' as handling
        union all select 'Marketing months that do not exist',
               (select count(*) from quality.rejected_marketing_months), 36, 'left out'
        union all select 'Reservations dated after their event',
               (select count(*) from quality.flagged_reservation_dates), 18000, 'kept; no lead-time indicator'
        union all select 'Website days with more bookings than visitors',
               (select count(*) from quality.flagged_traffic_days), 365, 'conversion left empty'""")


@app.get("/api/models")
def models() -> dict:
    out = {}
    for name in ("forecast_revenue", "predict_confirmation", "segment_customers"):
        path = REPORTS / f"{name}.json"
        if path.exists():
            out[name] = json.loads(path.read_text())
    return out


@app.get("/api/questions")
def suggested_questions() -> list[dict]:
    """The assistant's /questions command: questions worth asking, their current answer, the decision each informs."""
    return questions.all_questions()


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@app.post("/api/ask")
def ask(body: Question) -> dict:
    try:
        return assistant.ask(body.question)
    except assistant.AssistantError as error:
        status = {"screen": 400, "guard": 400, "run": 422, "busy": 429}.get(error.stage, 503)
        raise HTTPException(status, {"stage": error.stage, "message": error.message}) from error
