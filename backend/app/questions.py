"""The questions worth asking, for the assistant's /questions command.

Each question carries its current answer, computed here by a fixed, reviewed query (never by the language model),
and the decision that answer informs. Selecting one in the interface asks the assistant for the full explanation.
"""

import json
from collections.abc import Callable

from .db import records


def _one(sql: str) -> dict:
    return records(sql)[0]


def _pct(x: float) -> str:
    return f"{x:.1f} %"


def _signed(x: float) -> str:
    return f"{x:+.1f} %"


def event_type_leader() -> str:
    r = _one("""select e.event_type as label, 100.0 * sum(f.revenue) / sum(sum(f.revenue)) over () as share
                from marts.fact_reservation f join marts.dim_event e using (event_id) group by 1 order by 2 desc""")
    return f"{r['label']}: {_pct(r['share'])} of revenue"


def growth() -> str:
    r = _one("""select 100.0 * sum(revenue) filter (where reservation_date >= '2025-01-01')
                  / sum(revenue) filter (where reservation_date between '2024-01-01' and '2024-12-31') - 100 as g
                from marts.fact_reservation""")
    return f"{_signed(r['g'])} in 2025 against 2024"


def governorate_leader() -> str:
    r = _one("""with t as (select g.governorate, g.population_2024 as pop, sum(f.revenue) as rev
                           from marts.fact_reservation f join marts.dim_geography g using (governorate_id)
                           group by 1, 2)
                select (select governorate from t order by rev desc limit 1) as top,
                       (select 100.0 * max(rev) / sum(rev) from t) as share, corr(pop, rev) as r from t""")
    return f"{r['top']} leads with {_pct(r['share'])}; revenue does not follow population (r = {r['r']:.2f})"


def confirmation() -> str:
    r = _one("""select 100.0 * avg(is_confirmed::int) as c, 100.0 * avg(is_cancelled::int) as x,
                       100.0 * avg((status = 'pending')::int) as p from marts.fact_reservation""")
    return f"{_pct(r['c'])} confirmed, {_pct(r['p'])} still pending, {_pct(r['x'])} cancelled"


def ramadan() -> str:
    # same comparison as analytics/eda.ipynb (Ramadan days against all other days), so its test applies: p = 0.10
    r = _one("""with d as (select d.is_ramadan, coalesce(sum(f.revenue), 0) as rev from marts.dim_date d
                           left join marts.fact_reservation f on f.reservation_date = d.date_day
                           group by d.date_day, d.is_ramadan)
                select 100.0 * avg(rev) filter (where is_ramadan) / avg(rev) filter (where not is_ramadan) - 100 as diff
                from d""")
    return f"{_signed(r['diff'])} revenue per day during Ramadan; not statistically significant (p = 0.10)"


def conversion() -> str:
    r = _one("""select 100.0 * percentile_cont(0.5) within group (order by conversion_rate) as m
                from reporting.rpt_site_traffic_daily where is_valid""")
    return f"median {r['m']:.1f} % of daily visitors book (2022)"


def satisfaction() -> str:
    r = _one("""select avg(rating_avg) as a, 100.0 * avg((rating_avg >= 4)::int) as hi
                from marts.fact_reservation where rating_avg is not null""")
    return f"average {r['a']:.2f} / 5; {_pct(r['hi'])} rated 4 or more"


def returning() -> str:
    r = _one("select 100.0 * avg(is_returning::int) as r from marts.dim_beneficiary where events > 0")
    return f"{_pct(r['r'])} of customers booked more than one event"


def complaints_region() -> str:
    r = _one("""select g.region, 100.0 * sum(p.complaints) / max(n.n) as per100
                from marts.dim_provider p join marts.dim_geography g using (governorate_id)
                join (select g2.region, count(*) as n from marts.fact_reservation f
                      join marts.dim_geography g2 using (governorate_id) group by 1) n on n.region = g.region
                group by 1 order by 2 desc""")
    return f"{r['region']}: {r['per100']:.1f} complaints per 100 reservations"


def marketing_cost() -> str:
    # pooled cost (total spend / total new customers), as in Metabase; a mean of monthly ratios over-weights
    # months with few new customers
    rows = records("""select spend_type, sum(marketing_spend) / nullif(sum(new_beneficiaries), 0) as cpc
                      from reporting.rpt_marketing_monthly group by 1 order by 2""")
    best, worst = rows[0], rows[-1]
    return (f"{best['spend_type']} months: {best['cpc']:.1f} per new customer, "
            f"against {worst['cpc']:.1f} in {worst['spend_type']} months")


def _report(name: str) -> dict:
    from .main import REPORTS as reports_dir  # late import: main imports this module

    return json.loads((reports_dir / f"{name}.json").read_text())


def forecast() -> str:
    r = _report("forecast_revenue")
    months = r["forecast"]
    total = sum(m["revenue"] for m in months)
    return f"about {total:,.0f} over {months[0]['month']} to {months[-1]['month']} ({r['chosen_model']})"


def not_converted() -> str:
    seg = next(s for s in _report("segment_customers")["segments"] if s["name"] == "Not yet converted")
    return f"{seg['customers']:,} customers ({_pct(100 * seg['share'])}) booked but never confirmed"


def excluded() -> str:
    r = _one("""select (select count(*) from quality.rejected_evaluations) as ratings,
                       (select count(*) from quality.flagged_reservation_dates) as dates""")
    return f"{r['ratings']} ratings left out; {r['dates']:,} reservations dated after their event flagged"


QUESTIONS: list[tuple[str, str, str, Callable[[], str]]] = [
    ("revenue", "Is revenue growing?",
     "Whether current growth can carry new spending, or the budget should hold.", growth),
    ("revenue", "Which event type brings the most revenue?",
     "Where to recruit providers and focus promotion first.", event_type_leader),
    ("revenue", "Which governorates earn the most, and does it follow population?",
     "Whether to target regions by size or by results.", governorate_leader),
    ("revenue", "What will revenue be over the next six months?",
     "The revenue line of next half-year's budget.", forecast),
    ("reservations", "How many reservations end up confirmed?",
     "Whether following up pending bookings is worth a dedicated person.", confirmation),
    ("reservations", "Does Ramadan lower revenue?",
     "Whether to plan campaigns and staffing around the calendar.", ramadan),
    ("reservations", "How many website visitors book?",
     "Whether to invest in the website or in bringing more visitors.", conversion),
    ("customers", "Are customers satisfied?",
     "Whether service quality needs action before growth.", satisfaction),
    ("customers", "How many customers come back?",
     "Whether to fund a loyalty offer or focus on new customers.", returning),
    ("customers", "Who booked but never confirmed?",
     "Whom a conversion follow-up campaign should target.", not_converted),
    ("customers", "Which region has the most complaints?",
     "Where to review providers first.", complaints_region),
    ("marketing", "Which level of marketing spend brings new customers cheapest?",
     "How to set next year's marketing budget.", marketing_cost),
    ("quality", "How much data was left out, and why?",
     "How far to trust the figures before presenting them.", excluded),
]


def all_questions() -> list[dict]:
    out = []
    for i, (objective, question, decision, compute) in enumerate(QUESTIONS, 1):
        try:
            value = compute()
        except (LookupError, OSError, ValueError, TypeError, ZeroDivisionError):
            value = None  # a missing report or empty table: the question stays, without a figure
        out.append({"id": i, "objective": objective, "question": question, "value": value, "decision": decision})
    return out
