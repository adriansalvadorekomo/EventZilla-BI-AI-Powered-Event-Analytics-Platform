"""Integration tests against the running warehouse (skipped without ANALYST_DB_PASSWORD)."""

import os

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(not os.environ.get("ANALYST_DB_PASSWORD"), reason="needs the warehouse")


@pytest.fixture(scope="module")
def client():
    from app.main import app

    return TestClient(app)


def test_overview_matches_the_star(client):
    o = client.get("/api/overview").json()
    assert o["reservations"] == 18000
    assert 0 < o["confirmation_rate"] < 100 and 1 <= o["average_rating"] <= 5


@pytest.mark.parametrize("path", ["/api/revenue/monthly", "/api/revenue/by/event_type", "/api/revenue/by/region",
                                  "/api/revenue/by/service", "/api/revenue/by/governorate", "/api/reservations/status",
                                  "/api/reservations/calendar", "/api/conversion/weekly", "/api/quality"])
def test_series_are_not_empty(client, path):
    r = client.get(path)
    assert r.status_code == 200 and len(r.json()) > 0


def test_monthly_revenue_covers_four_years(client):
    assert len(client.get("/api/revenue/monthly").json()) == 48


def test_unknown_dimension_is_404(client):
    assert client.get("/api/revenue/by/weather").status_code == 404


def test_models_reports_are_served(client):
    m = client.get("/api/models").json()
    assert {"forecast_revenue", "predict_confirmation", "segment_customers"} <= set(m)


def test_metrics_are_exposed(client):
    assert "http_requests_total" in client.get("/metrics").text


def test_governorates_cover_all_revenue(client):
    rows = client.get("/api/revenue/by/governorate").json()
    overview = client.get("/api/overview").json()
    assert len(rows) == 24 and round(sum(r["revenue"] for r in rows)) == round(overview["revenue"])
    assert all(r["region"] and r["revenue_per_1000_inhabitants"] > 0 for r in rows)


def test_questions_carry_a_value_and_a_decision(client):
    qs = client.get("/api/questions").json()
    assert len(qs) >= 12 and {q["objective"] for q in qs} >= {"revenue", "reservations", "customers", "marketing"}
    assert all(q["value"] and q["decision"] for q in qs)
