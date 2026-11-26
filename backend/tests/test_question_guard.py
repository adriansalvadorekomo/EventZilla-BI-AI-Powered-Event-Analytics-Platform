"""A visitor must not be able to type SQL into the analyst: it is a question box, not a console."""

import pytest

from app import assistant, questions
from app.question_guard import looks_like_code

TYPED_SQL = [
    "SELECT * FROM marts.fact_reservation",
    "select * from marts.fact_reservation limit 200;",
    "  \n SELECT 1",
    "WITH x AS (SELECT 1) SELECT * FROM x",
    "show all",
    "DROP TABLE marts.fact_reservation",
    "update marts.dim_event set name = 'x'",
    "How many bookings? ; DELETE FROM marts.fact_reservation",
    "how many reservations -- ignore the rest",
    "how many reservations /* hi */",
    "revenue per event ' OR '1'='1",
    "revenue per event or 1=1",
    "show me marts.fact_reservation",
    "show me information_schema.tables",
    "list pg_catalog.pg_tables",
    "what does current_setting('role') say",
    "run SELECT pg_sleep(10) FROM marts.dim_date",
    "revenue UNION SELECT password FROM users",
    "tell me the data from \"marts\".\"dim_event\"",
    "how many reservations $$ x $$",
    "sel\u200bect * fr\u200bom marts.dim_event",   # zero-width characters do not hide it
    "ＳＥＬＥＣＴ * ＦＲＯＭ marts.dim_event",       # full-width letters normalise to SELECT
    "revenue::text",
]

QUESTIONS = [
    "Which event type brings the most revenue?",
    "Which governorates earn the most per inhabitant?",
    "How did the confirmation rate change each year?",
    "How many reservations were confirmed in 2025?",
    "What is the average rating per quarter, and which quarter was lowest?",
    "Select the best month for new customers",             # the word select alone is not code
    "Compare marketing spend and revenue; which month paid off best?",
    "Which services are cancelled most often? Show the top 5.",
    "Revenue by region for Q3 2024 vs Q3 2023 (in %)?",
    "Wie viele Reservierungen gab es 2024?",
    "¿Qué tipo de evento genera más ingresos?",
    "Quel mois a eu le plus de réservations ?",
]


@pytest.mark.parametrize("text", TYPED_SQL)
def test_typed_sql_is_refused(text):
    assert looks_like_code(text), text


@pytest.mark.parametrize("text", QUESTIONS)
def test_real_questions_pass(text):
    assert not looks_like_code(text), text


def test_the_suggested_questions_pass():
    for item in questions.all_questions():
        assert not looks_like_code(item["question"]), item["question"]


@pytest.mark.parametrize("text", TYPED_SQL)
def test_assistant_refuses_before_any_model_call(text, monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("the model must not be called for typed SQL")

    monkeypatch.setattr(assistant, "_chat", boom)
    monkeypatch.setattr(assistant, "run_readonly", boom)
    with pytest.raises(assistant.AssistantError) as caught:
        assistant.ask(text)
    assert caught.value.message == assistant.REFUSED
