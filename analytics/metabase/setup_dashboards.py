"""Metabase dashboards as code: one per business objective (docs/GIMSI.md), plus data quality.

    MB_URL=http://127.0.0.1:3001 MB_API_KEY=... python analytics/metabase/setup_dashboards.py

First run on a fresh Metabase: also set MB_SETUP=1 (creates the admin with MB_USER / MB_PASSWORD and connects the
warehouse from the WAREHOUSE_* variables). Re-running replaces the "EventZilla" collection, so the dashboards
always match this file. Prints the public (night theme) link of each dashboard.

Language is for decision-makers: each card asks the question it answers. Colour: one orange signal per chart
(the series that answers the question), light ink for the rest.
"""

import os

import requests

URL = os.environ.get("MB_URL", "http://127.0.0.1:3001").rstrip("/")
SIGNAL, INK, INK3 = "#ff4f00", "#c4c0b7", "#8a867e"
S = requests.Session()


def api(method: str, path: str, **kw):
    r = S.request(method, f"{URL}/api{path}", timeout=120, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path}: {r.status_code} {r.text[:300]}")
    return r.json() if r.text else None


def setup() -> None:
    token = api("GET", "/session/properties")["setup-token"]
    api("POST", "/setup", json={
        "token": token,
        "user": {"email": os.environ["MB_USER"], "password": os.environ["MB_PASSWORD"],
                 "first_name": "EventZilla", "last_name": "Admin", "site_name": "EventZilla"},
        "prefs": {"site_name": "EventZilla", "site_locale": "en", "allow_tracking": False},
    })


def login() -> None:
    """An API key (Admin settings > Authentication > API keys, group Administrators) is preferred: no password."""
    if os.environ.get("MB_API_KEY"):
        S.headers["X-API-Key"] = os.environ["MB_API_KEY"]
        return
    S.headers["X-Metabase-Session"] = api("POST", "/session", json={
        "username": os.environ["MB_USER"], "password": os.environ["MB_PASSWORD"]})["id"]


def warehouse_id() -> int:
    for db in api("GET", "/database")["data"]:
        if db["name"] == "EventZilla warehouse":
            return db["id"]
    return api("POST", "/database", json={
        "name": "EventZilla warehouse", "engine": "postgres",
        "details": {"host": os.environ.get("WAREHOUSE_HOST", "warehouse"), "port": 5432, "dbname": "eventzilla",
                    "user": os.environ.get("WAREHOUSE_USER", "eventzilla"),
                    "password": os.environ["WAREHOUSE_PASSWORD"],
                    "schema-filters-type": "inclusion", "schema-filters-patterns": "marts,reporting,quality"}})["id"]


# ── cards ───────────────────────────────────────────────────────────────────
def line(x, ys, signal, y_title="", stacked=False):
    return {"graph.dimensions": [x], "graph.metrics": ys, "graph.x_axis.title_text": "",
            "graph.y_axis.title_text": y_title, "graph.show_values": False,
            "line.marker_enabled": False, "line.interpolate": "linear",
            **({"stackable.stack_type": "stacked"} if stacked else {}),
            "series_settings": {y: {"color": SIGNAL if y == signal else INK} for y in ys}}


def bar(x, y, y_title="", color=INK, y_max=None):
    s = {"graph.dimensions": [x], "graph.metrics": [y], "graph.x_axis.title_text": "",
         "graph.y_axis.title_text": y_title, "graph.show_values": True,
         "series_settings": {y: {"color": color}}}
    if y_max is not None:
        s.update({"graph.y_axis.auto_range": False, "graph.y_axis.min": 0, "graph.y_axis.max": y_max})
    return s


def scalar(suffix="", prefix="", decimals=None):
    s = {"scalar.suffix": suffix, "scalar.prefix": prefix}
    if decimals is not None:
        s["scalar.decimals"] = decimals
    return s


REV_MONTH = """select date_trunc('month', reservation_date)::date as month, sum(revenue) as "Confirmed revenue"
from marts.fact_reservation group by 1 order by 1"""

DASHBOARDS = [
    ("1 · Revenue and profitability", "BO1 · Is the business making money, and where does it come from?", [
        ("Confirmed revenue", "Final price of confirmed reservations, 2022-2025.", "scalar",
         "select sum(revenue) as revenue from marts.fact_reservation", scalar(decimals=0), (0, 0, 6, 4)),
        ("Growth, 2025 vs 2024", "Change in confirmed revenue between the last two years of data.",
         "scalar", """select round(100.0 * (sum(revenue) filter (where reservation_date >= '2025-01-01'))
              / nullif(sum(revenue) filter (where reservation_date between '2024-01-01' and '2024-12-31'), 0) - 100, 1)
              as change from marts.fact_reservation""", scalar(suffix=" %", decimals=1), (6, 0, 6, 4)),
        ("Average booking", "Mean final price of a confirmed reservation.", "scalar",
         "select round(avg(final_price)) as avg from marts.fact_reservation where is_confirmed",
         scalar(decimals=0), (12, 0, 6, 4)),
        ("Confirmed bookings", "Reservations that were confirmed.", "scalar",
         "select count(*) as n from marts.fact_reservation where is_confirmed", scalar(decimals=0), (18, 0, 6, 4)),
        ("How does confirmed revenue move month to month?", "Flat over four years, with monthly swings.", "line",
         REV_MONTH, line("month", ["Confirmed revenue"], "Confirmed revenue"), (0, 4, 24, 7)),
        ("Which events earn the most?", "Confirmed revenue by event type.", "bar",
         """select e.event_type as "Event type", sum(f.revenue) as "Confirmed revenue"
            from marts.fact_reservation f join marts.dim_event e using (event_id) group by 1 order by 2 desc""",
         bar("Event type", "Confirmed revenue"), (0, 11, 12, 6)),
        ("Which services earn the most?", "Confirmed revenue by service category.", "bar",
         """select s.service_category as "Service", sum(f.revenue) as "Confirmed revenue"
            from marts.fact_reservation f join marts.dim_service s using (service_id) group by 1 order by 2 desc""",
         bar("Service", "Confirmed revenue"), (12, 11, 12, 6)),
        ("Where is revenue earned, relative to population?",
         "Confirmed revenue per 1,000 inhabitants by region: the view for deciding where to recruit providers.",
         "row", """select g.region as "Region",
                   round(sum(f.revenue) * 1000.0 / max(r.pop)) as "Revenue per 1,000 inhabitants"
            from marts.fact_reservation f join marts.dim_geography g using (governorate_id)
            join (select region, sum(population_2024) pop from marts.dim_geography group by 1) r using (region)
            group by 1 order by 2 desc""", bar("Region", "Revenue per 1,000 inhabitants"), (0, 17, 12, 6)),
        ("Top 10 events by confirmed revenue", "With the budget the customer announced.", "table",
         """select e.event_type as "Type", e.event_date as "Date", sum(f.revenue) as "Confirmed revenue"
            from marts.fact_reservation f join marts.dim_event e using (event_id)
            group by e.event_id, 1, 2 order by 3 desc limit 10""", {}, (12, 17, 12, 6)),
    ]),
    ("2 · Reservations and conversion", "BO2 · How many reservations turn into business?", [
        ("Confirmation rate", "Share of reservations confirmed.", "scalar",
         "select round(100.0 * avg(is_confirmed::int), 1) as rate from marts.fact_reservation",
         scalar(suffix=" %", decimals=1), (0, 0, 8, 4)),
        ("Cancellation rate", "Share of reservations cancelled.", "scalar",
         "select round(100.0 * avg(is_cancelled::int), 1) as rate from marts.fact_reservation",
         scalar(suffix=" %", decimals=1), (8, 0, 8, 4)),
        ("Website conversion", ("Reservations per visitor on a typical day; the baseline for the"
         " +15 % target. Impossible days are excluded."), "scalar",
         ("select round(100.0 * percentile_cont(0.5) within group (order by conversion_rate)::numeric, 1) as conv "
         "from reporting.rpt_site_traffic_daily where is_valid"), scalar(suffix=" %", decimals=1), (16, 0, 8, 4)),
        ("Where do reservations end up, quarter by quarter?", "Share of reservations by status.", "line",
         """select date_trunc('quarter', reservation_date)::date as quarter,
                   round(100.0 * avg(is_confirmed::int), 1) as "Confirmed %",
                   round(100.0 * avg((status = 'pending')::int), 1) as "Pending %",
                   round(100.0 * avg(is_cancelled::int), 1) as "Cancelled %"
            from marts.fact_reservation group by 1 order by 1""",
         line("quarter", ["Confirmed %", "Pending %", "Cancelled %"], "Confirmed %", "% of reservations"),
         (0, 4, 24, 7)),
        ("Do Ramadan and public holidays change daily revenue?",
         ("Average confirmed revenue per day. Ramadan -11 %, holidays -10 %: not statistically significant "
         "(p = 0.10 and 0.15, see analytics/eda.ipynb)."), "bar",
         """with d as (select d.date_day, d.is_ramadan, d.is_holiday, coalesce(sum(f.revenue), 0) rev
                       from marts.dim_date d left join marts.fact_reservation f on f.reservation_date = d.date_day
                       group by 1, 2, 3)
            select case when is_ramadan then 'Ramadan' when is_holiday then 'Public holiday' else 'Other days' end
                   as "Days", round(avg(rev)) as "Revenue per day" from d group by 1 order by 2 desc""",
         bar("Days", "Revenue per day"), (0, 11, 12, 6)),
        ("Website conversion through 2022", "Weekly median of reservations per visitor.", "line",
         """select date_trunc('week', traffic_date)::date as week,
                   round(100.0 * percentile_cont(0.5) within group (order by conversion_rate)::numeric, 2)
                     as "Conversion %"
            from reporting.rpt_site_traffic_daily where is_valid group by 1 order by 1""",
         line("week", ["Conversion %"], "Conversion %", "%"), (12, 11, 12, 6)),
    ]),
    ("3 · Satisfaction and retention", "BO3 · Are customers satisfied, and do they come back?", [
        ("Average rating", "Valid evaluations only (1 to 5).", "scalar",
         "select round(avg(rating_avg), 2) as r from marts.fact_reservation", scalar(suffix=" / 5", decimals=2),
         (0, 0, 6, 4)),
        ("Rated 4 or more", "Share of evaluated reservations.", "scalar",
         ("select round(100.0 * avg((rating_avg >= 4)::int), 1) as s from marts.fact_reservation "
         "where rating_avg is not null"), scalar(suffix=" %", decimals=1), (6, 0, 6, 4)),
        ("Returning customers", "Customers with two events or more; the baseline for the +20 % target.", "scalar",
         "select round(100.0 * avg(is_returning::int), 1) as s from marts.dim_beneficiary where events > 0",
         scalar(suffix=" %", decimals=1), (12, 0, 6, 4)),
        ("Open complaints", "Complaints not yet closed.", "scalar",
         "select sum(complaints) from reporting.rpt_complaint_summary where status = 'open'", scalar(decimals=0),
         (18, 0, 6, 4)),
        ("Where do customers complain most?", "Complaints per 100 reservations by region.", "row",
         """select g.region as "Region",
                   round(100.0 * sum(p.complaints) / max(r.n), 1) as "Complaints per 100 reservations"
            from marts.dim_provider p join marts.dim_geography g using (governorate_id)
            join (select g2.region, count(*) n from marts.fact_reservation f
                  join marts.dim_geography g2 using (governorate_id) group by 1) r on r.region = g.region
            group by 1 order by 2 desc""", bar("Region", "Complaints per 100 reservations"),
         (0, 4, 12, 7)),
        ("What do customers complain about?", "Complaints by subject and status.", "bar",
         """select subject as "Subject", sum(complaints) filter (where status = 'open') as "Open",
                   sum(complaints) filter (where status = 'closed') as "Closed"
            from reporting.rpt_complaint_summary group by 1 order by 2 desc""",
         line("Subject", ["Open", "Closed"], "Open", stacked=True), (12, 4, 12, 7)),
        ("How do customers rate each service?", "Average valid rating by service category.", "bar",
         """select s.service_category as "Service", round(avg(f.rating_avg), 2) as "Average rating"
            from marts.fact_reservation f join marts.dim_service s using (service_id)
            where f.rating_avg is not null group by 1 order by 2 desc""", bar("Service", "Average rating", y_max=5),
         (0, 11, 24, 6)),
    ]),
    ("4 · Marketing return", "BO4 · Does marketing spend bring customers and revenue? (2023-2024, valid months)", [
        ("Marketing spend, 2023-2024", "Total over the 24 valid months.", "scalar",
         "select sum(marketing_spend) from reporting.rpt_marketing_monthly", scalar(decimals=0), (0, 0, 8, 4)),
        ("New customers, 2023-2024", "Reported by the marketing source.", "scalar",
         "select sum(new_beneficiaries) from reporting.rpt_marketing_monthly", scalar(decimals=0), (8, 0, 8, 4)),
        ("Cost per new customer", "Spend divided by new customers, all campaigns.", "scalar",
         ("select round(sum(marketing_spend) / nullif(sum(new_beneficiaries), 0), 1) "
          "from reporting.rpt_marketing_monthly"),
         scalar(decimals=1), (16, 0, 8, 4)),
        ("Does revenue follow marketing spend?",
         "Monthly spend and confirmed revenue. No significant link (rho = -0.19, p = 0.37; see analytics/eda.ipynb).",
         "line", """select month_start as month, marketing_spend as "Marketing spend",
                          confirmed_revenue as "Confirmed revenue" from reporting.rpt_marketing_monthly order by 1""",
         line("month", ["Marketing spend", "Confirmed revenue"], "Confirmed revenue"), (0, 4, 24, 7)),
        ("Which campaigns recruit customers cheapest?", "Average cost per new customer by campaign type.", "bar",
         """select spend_type as "Campaign type", round(sum(marketing_spend) / nullif(sum(new_beneficiaries), 0), 1)
                   as "Cost per new customer" from reporting.rpt_marketing_monthly group by 1 order by 2""",
         bar("Campaign type", "Cost per new customer"), (0, 11, 24, 6)),
    ]),
    ("5 · Data quality", "What was excluded or flagged before these numbers were computed, and why.", [
        ("Rows quarantined or flagged by the quality rules", "Every rule, its rows and its share of the source.",
         "table", """select 'Evaluation ratings outside 1-5 (left out of averages)' as "Rule",
                   (select count(*) from quality.rejected_evaluations) as "Rows", 12000 as "Of"
            union all select 'Marketing rows that are not a calendar month (left out)',
                   (select count(*) from quality.rejected_marketing_months), 36
            union all select 'Reservations dated after their event (kept; no lead-time indicator)',
                   (select count(*) from quality.flagged_reservation_dates), 18000
            union all select 'Website days with more reservations than visitors (conversion left empty)',
                   (select count(*) from quality.flagged_traffic_days), 365""", {}, (0, 0, 24, 6)),
    ]),
]


# Plain-language takeaways under each dashboard; every figure is checked in analytics/eda.ipynb.
NOTE = "*The data is synthetic: read differences as patterns in this dataset, not as market facts.*"
TAKEAWAYS = {
    "1 · Revenue and profitability": (
        "**What this tells us.** Confirmed revenue is steady at 14.7M to 15.4M a year (+4.4 % in 2025). Weddings "
        "earn the most (26.7 %), but every event type and service is within a few points of the others. Per "
        "inhabitant, the South West earns 2.5 times what the North East does: the region to recruit providers "
        "in next. " + NOTE),
    "2 · Reservations and conversion": (
        "**What this tells us.** A third of reservations are confirmed, a third cancelled and a third left "
        "pending, every quarter since 2022. Daily revenue is 11 % lower during Ramadan and 10 % lower on public "
        "holidays, but neither gap is statistically significant (p = 0.10 and 0.15). A typical day of 2022 "
        "converted 5.4 % of website visitors: the baseline for the +15 % reservation target. " + NOTE),
    "3 · Satisfaction and retention": (
        "**What this tells us.** Half the reservations were evaluated; their ratings average 2.99 out of 5 and "
        "barely differ by service, and about a third score 4 or more. 76 % of customers came back for a second "
        "event: the baseline for the +20 % retention target. Complaints run at 13 to 16 per 100 reservations, "
        "highest in the North West, and half are still open. " + NOTE),
    "4 · Marketing return": (
        "**What this tells us.** Over the 24 valid months, spend shows no significant link to revenue "
        "(rho = -0.19, p = 0.37) or to new customers (rho = 0.18, p = 0.40). What a manager can act on is the "
        "cost of a new customer: 19.5 for normal campaigns, 63.8 for expensive ones, for about the same number "
        "of new customers a month (1,173 vs 1,180). " + NOTE),
    "5 · Data quality": (
        "**Why this matters.** These rows were excluded or flagged before any number on the other dashboards was "
        "computed. Ratings of 6, 9, 12 and 15 look like a scaling error at the source; half the reservations are "
        "dated after their own event, so no lead-time indicator is shown anywhere."),
}


def main() -> None:
    if os.environ.get("MB_SETUP"):
        setup()
    login()
    db = warehouse_id()
    api("POST", f"/database/{db}/sync_schema")
    api("PUT", "/setting/enable-public-sharing", json={"value": True})
    for c in api("GET", "/collection"):
        if c.get("name") == "EventZilla" and not c.get("archived"):
            api("PUT", f"/collection/{c['id']}", json={"archived": True})
    coll = api("POST", "/collection", json={
        "name": "EventZilla", "color": SIGNAL,
        "description": "One dashboard per business objective (docs/GIMSI.md)"})["id"]
    for title, subtitle, cards in DASHBOARDS:
        dash = api("POST", "/dashboard", json={"name": title, "description": subtitle, "collection_id": coll})
        dashcards = []
        for i, (name, desc, display, sql, viz, (col, row, w, h)) in enumerate(cards):
            card = api("POST", "/card", json={
                "name": name, "description": desc, "display": display, "collection_id": coll,
                "dataset_query": {"type": "native", "native": {"query": sql}, "database": db},
                "visualization_settings": viz})
            dashcards.append({"id": -(i + 1), "card_id": card["id"], "col": col, "row": row,
                              "size_x": w, "size_y": h})
        bottom = max(row + h for *_, (col, row, w, h) in cards)
        dashcards.append({"id": -(len(cards) + 1), "card_id": None, "col": 0, "row": bottom, "size_x": 24,
                          "size_y": 4, "visualization_settings": {
                              "virtual_card": {"name": None, "display": "text", "visualization_settings": {},
                                               "dataset_query": {}, "archived": False},
                              "text": TAKEAWAYS[title]}})
        api("PUT", f"/dashboard/{dash['id']}", json={"dashcards": dashcards})
        uuid = api("POST", f"/dashboard/{dash['id']}/public_link")["uuid"]
        print(f"{title:36} {URL}/public/dashboard/{uuid}#theme=night")


if __name__ == "__main__":
    main()
