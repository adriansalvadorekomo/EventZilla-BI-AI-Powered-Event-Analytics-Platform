# n8n workflows

Airflow runs the data pipeline; n8n runs the business automation around it. Three workflows, versioned here and
loaded with `mise run n8n:import` (imports and publishes them in the running n8n container).

| Workflow | Trigger | What it does |
|---|---|---|
| `freshness-watch.json` · data freshness watch | every hour, or called by another workflow | reads `/api/status`; if the figures are more than 26 h old or the star schema failed its gate, the execution fails with "EventZilla figures must not be presented: …" (wire n8n's error workflow to Slack, Teams or email to be told) |
| `decision-brief.json` · weekly decision brief | Monday 07:00, or `GET /webhook/decision-brief` | reads `/api/status` and `/api/questions` and writes a Markdown brief: each objective's questions with today's answer and the decision it informs, and whether the figures passed the gate |
| `ask-the-analyst.json` · ask the analyst | `POST /webhook/ask` with `{"question": "…"}` | forwards the question to the analyst (`/api/ask`) and returns the answer, the row count and the SQL; the doorway for a chat integration |

Verified on 2026-11-24:
- the brief listed all 13 questions with the gate line;
- the ask webhook answered "How many customers come back?" with its SQL;
- the watch passed on fresh data, then failed as designed on a test gate result of 14 of 15 (the test row was then deleted).

All three call the API inside the compose network (`http://api:8000`) and hold no credentials.
