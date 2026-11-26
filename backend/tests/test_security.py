"""API security that needs no database: nothing about how an answer was found leaves the server, errors are one
plain line, the public surface is only the data endpoints, and the rate limit cannot be dodged with a forged header."""

import pytest
from fastapi.testclient import TestClient

from app import assistant, main
from app.ratelimit import SlidingWindow

QUERY_TEXT = "SELECT SUM(revenue) FROM marts.fact_reservation LIMIT 200"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "ask_limiter", SlidingWindow(limit=100, window_s=60, instance_limit=1000))
    return TestClient(main.app, raise_server_exceptions=False)


def full_answer(question="q"):
    return {"question": question, "answer": "15.9 million.", "sql": QUERY_TEXT, "columns": ["Revenue"],
            "rows": [[15892996]], "chart": {"type": "number"}, "title": "Revenue", "screen_risk": 0.0004,
            "repaired": True, "elapsed_ms": 1200}


def test_an_answer_never_carries_the_query_or_how_it_was_found(client, monkeypatch):
    monkeypatch.setattr(assistant, "ask", lambda q: full_answer(q))
    r = client.post("/api/ask", json={"question": "How much revenue?"})
    assert r.status_code == 200
    assert set(r.json()) == {"question", "answer", "columns", "rows", "chart", "title", "elapsed_ms"}
    assert "SELECT" not in r.text.upper() and "screen_risk" not in r.text and "repaired" not in r.text


def test_a_refusal_says_nothing_about_the_guard(client, monkeypatch):
    def refuse(_q):
        raise assistant.AssistantError("guard", assistant.REFUSED, "query refused: function pg_sleep is not allowed")
    monkeypatch.setattr(assistant, "ask", refuse)
    r = client.post("/api/ask", json={"question": "do something odd"})
    assert r.status_code == 400
    assert r.json()["detail"]["message"] == assistant.REFUSED
    assert "pg_sleep" not in r.text and "function" not in r.text


def test_an_unexpected_failure_in_the_analyst_is_one_plain_line(client, monkeypatch):
    def fail(_q):
        raise RuntimeError("connection to ep-secret-host.neon.tech failed, password=hunter2")
    monkeypatch.setattr(assistant, "ask", fail)
    r = client.post("/api/ask", json={"question": "anything at all"})
    assert r.status_code == 503
    assert "secret-host" not in r.text and "hunter2" not in r.text


def test_an_unexpected_failure_in_a_data_endpoint_is_one_plain_line(client, monkeypatch):
    def fail(*_a, **_k):
        raise RuntimeError("FATAL: password authentication failed for user analyst_ro (host ep-x)")
    monkeypatch.setattr(main, "records", fail)
    r = client.get("/api/overview")
    assert r.status_code == 500 and r.json() == {"detail": "Something went wrong."}


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json", "/metrics"])
def test_no_docs_schema_or_metrics_on_a_public_deployment(client, path):
    assert client.get(path).status_code == 404


def test_responses_carry_security_headers(client):
    r = client.get("/api/models")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert r.headers["referrer-policy"] == "no-referrer"


def test_answers_are_never_cached(client, monkeypatch):
    monkeypatch.setattr(assistant, "ask", lambda q: full_answer(q))
    assert client.post("/api/ask", json={"question": "How much revenue?"}).headers["cache-control"] == "no-store"


@pytest.mark.parametrize("dimension", ["region'; drop table marts.dim_date; --", "1 or 1=1", "../../etc/passwd",
                                       "region) union select password from pg_authid --"])
def test_a_path_parameter_cannot_reach_sql(client, monkeypatch, dimension):
    monkeypatch.setattr(main, "records", lambda *_a, **_k: pytest.fail("the query must not run"))
    assert client.get(f"/api/revenue/by/{dimension}").status_code in {404, 422}


@pytest.mark.parametrize("body", [{}, {"question": ""}, {"question": "ab"}, {"question": "x" * 501},
                                  {"question": ["select 1"]}, {"question": {"$ne": 1}}])
def test_the_question_is_validated(client, body):
    assert client.post("/api/ask", json=body).status_code == 422


def test_the_rate_limit_cannot_be_dodged_with_a_forged_forwarded_header(monkeypatch):
    monkeypatch.setattr(main, "ask_limiter", SlidingWindow(limit=2, window_s=60, instance_limit=1000))
    monkeypatch.setattr(assistant, "ask", lambda q: full_answer(q))
    c = TestClient(main.app, raise_server_exceptions=False)
    codes = [c.post("/api/ask", json={"question": "How much revenue?"},
                    headers={"X-Forwarded-For": f"10.0.0.{i}, 203.0.113.9"}).status_code for i in range(4)]
    assert codes == [200, 200, 429, 429]           # the first entry changes every time; the real address does not


def test_a_stranger_origin_gets_no_cors_permission(client):
    r = client.get("/api/models", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers
