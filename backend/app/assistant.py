"""The analyst assistant: a business question in, a checked answer out.

1. screen   Llama Prompt Guard 2 scores the question for prompt injection (blocked above 0.5)
2. write    gpt-oss-120b writes one SELECT against the semantic layer, and proposes a chart
3. guard    sql_guard: one read-only SELECT on the analytics schemas, row limit
4. run      as analyst_ro (read-only role, 5 s timeout); if Postgres rejects the query, the error goes back to the
            writer once for a repair, and the repaired query is guarded again
5. explain  gpt-oss-120b turns the rows actually returned into two or three plain sentences

Every step is reported back, so the interface can show what was asked, what ran and why.
"""

import json
import os
import time

import httpx
from sqlalchemy.exc import DBAPIError

from .db import run_readonly
from .semantic import SEMANTIC_LAYER
from .sql_guard import UnsafeSQL, guard

GROQ = "https://api.groq.com/openai/v1/chat/completions"
WRITER = os.environ.get("ASSISTANT_MODEL", "openai/gpt-oss-120b")
SCREEN = "meta-llama/llama-prompt-guard-2-86m"
INJECTION_THRESHOLD = 0.5
MAX_WAIT_S = 10  # longest Retry-After we wait through on a rate limit

# prompt text for the model (never executed): the SQL it leads to goes through sql_guard and a read-only role
WRITE_PROMPT = f"""You are the analyst of EventZilla, an event-services company. Answer business questions by
writing ONE PostgreSQL SELECT query on the warehouse described below.
{SEMANTIC_LAYER}
Rules: only SELECT; only the schemas above; name columns in plain English with double quotes (for example
"Confirmed revenue"); round numbers sensibly; order results meaningfully; at most 200 rows. For "which ... most"
questions return every group, ranked, so the comparison is visible; for changes over time include the change in %.
Reply with JSON only: {{"sql": "...", "chart": {{"type": "line" | "bar" | "number" | "table", "x": "<column>",
"y": "<column>"}}, "title": "<short title for the result, in sentence case>"}}.
If the question cannot be answered from this data, reply {{"sql": null, "reason": "<why, in one sentence>"}}."""  # noqa: S608  # nosec B608 (prompt text, never executed)

EXPLAIN_PROMPT = """You explain analysis results to managers of an event-services company. In two or three short
sentences, answer the question from the rows given: lead with the answer, quote the key figures, no jargon, no SQL.
If the rows compare groups and the differences are small, say so. Do not invent figures that are not in the rows.
Plain text only (no markdown, no quotes around numbers). Write large numbers readably: 15.9 million, 14,912 (never
15892996). Describe changes with their size in %: call a change under
5 % small or modest, never sharp. Amounts have no documented currency: never add a currency symbol or name."""


class AssistantError(Exception):
    def __init__(self, stage: str, message: str):
        super().__init__(message)
        self.stage, self.message = stage, message


def _chat(model: str, messages: list[dict], json_mode: bool = False) -> str:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise AssistantError("config", "The assistant is not configured (no GROQ_API_KEY).")
    body = {"model": model, "messages": messages, "temperature": 0}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    for attempt in range(2):
        r = httpx.post(GROQ, json=body, headers={"Authorization": f"Bearer {key}"}, timeout=60)
        if r.status_code != 429:
            break
        wait = float(r.headers.get("retry-after", "2"))
        if attempt or wait > MAX_WAIT_S:
            raise AssistantError("busy", f"The assistant is busy; try again in {round(wait)} s.")
        time.sleep(wait)
    if r.status_code >= 400:
        raise AssistantError("model", f"The language model returned {r.status_code}.")
    return r.json()["choices"][0]["message"]["content"]


def _plan(messages: list[dict]) -> dict:
    try:
        return json.loads(_chat(WRITER, messages, json_mode=True))
    except json.JSONDecodeError as error:
        raise AssistantError("model", "The language model did not return a usable plan.") from error


def _guarded(sql: str) -> str:
    try:
        return guard(sql)
    except UnsafeSQL as error:
        raise AssistantError("guard", f"The generated query was refused: {error}.") from error


def screen(question: str) -> float:
    """Injection probability from Prompt Guard (0 safe, 1 attack)."""
    try:
        return float(_chat(SCREEN, [{"role": "user", "content": question}]).strip())
    except ValueError as error:
        raise AssistantError("screen", "The question could not be screened.") from error


def ask(question: str) -> dict:
    started = time.perf_counter()
    question = question.strip()[:500]
    risk = screen(question)
    if risk > INJECTION_THRESHOLD:
        raise AssistantError("screen", "This looks like an attempt to change the assistant's instructions.")

    messages = [{"role": "system", "content": WRITE_PROMPT}, {"role": "user", "content": question}]
    plan = _plan(messages)
    if not plan.get("sql"):
        return {"question": question, "answer": plan.get("reason", "This data cannot answer that question."),
                "sql": None, "columns": [], "rows": [], "chart": None, "title": None,
                "screen_risk": round(risk, 4), "elapsed_ms": round((time.perf_counter() - started) * 1000)}
    safe_sql, repaired = _guarded(plan["sql"]), False
    try:
        columns, rows = run_readonly(safe_sql)
    except DBAPIError as error:
        detail = str(error.orig).splitlines()[0] if error.orig else "query failed"
        plan = _plan([*messages, {"role": "assistant", "content": json.dumps(plan)},
                      {"role": "user", "content": f"PostgreSQL rejected that query: {detail}. Fix it; same JSON."}])
        if not plan.get("sql"):
            raise AssistantError("run", "The question could not be turned into a working query.") from error
        safe_sql, repaired = _guarded(plan["sql"]), True
        try:
            columns, rows = run_readonly(safe_sql)
        except DBAPIError as again:
            raise AssistantError("run", "The question could not be turned into a working query.") from again
    preview = json.dumps({"columns": columns, "rows": rows[:50]}, default=str)
    answer = _chat(WRITER, [{"role": "system", "content": EXPLAIN_PROMPT},
                            {"role": "user", "content": f"Question: {question}\nResult: {preview}"}])
    return {"question": question, "answer": answer.strip(), "sql": safe_sql, "columns": columns, "rows": rows,
            "chart": plan.get("chart"), "title": plan.get("title"), "screen_risk": round(risk, 4),
            "repaired": repaired, "elapsed_ms": round((time.perf_counter() - started) * 1000)}
