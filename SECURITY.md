# Security

EventZilla's data is synthetic, but the application is built as if it were not.

## What protects the analyst (the chat)

A visitor's question is turned into SQL by a language model. The model is not trusted; four independent layers hold:

1. **Screen:** the question is scored for prompt injection (probabilistic, so never the only control).
2. **Guard (`backend/app/sql_guard.py`):** an allow-list. One SELECT, on a fixed set of analytics tables, using a fixed
   set of functions, data types and constructs; bounded size, joins and rows. Anything unknown is refused, and an
   unexpected error in the guard itself refuses too. The query that runs is regenerated from the parsed tree,
   without comments.
3. **Transaction (`backend/app/db.py`):** read-only, 5 s statement timeout, short lock and idle timeouts, at most
   1,000 rows back.
4. **Database role (`analyst_ro`):** SELECT on four analytics schemas, no access to `raw` or `staging`.

Visitors never see the query, how it was found, or why a question was refused: answers carry the text, the chart
data and nothing else; errors are one plain line and the detail stays in the server log. `/api/ask` is rate limited
per visitor (the address comes from headers a client cannot forge) and per instance, and again in nginx.

`backend/tests/test_sql_guard_attacks.py` and `test_security.py` hold the attack payloads that once got through;
they run on every pull request.

## What protects the rest

- API: no interactive docs, schema or metrics on a public deployment; JSON-only security headers; CORS to the
  known origin only; request bodies validated (a question is 3 to 500 characters).
- Frontend: strict Content-Security-Policy (no inline or remote scripts), no framing, no raw HTML anywhere.
- Containers: the web image runs as an unprivileged user on a read-only filesystem with no extra capabilities;
  every port is bound to `127.0.0.1`; Airflow's public role is read-only; Grafana has no default login.
- Supply chain: CI fails on a vulnerable dependency (pip-audit, npm audit, Trivy), on a committed secret
  (Gitleaks over the whole history) and on an insecure Dockerfile; Dependabot opens the update pull requests.
- Secrets: only in `.env` (git-ignored). The deployed API receives only the two it needs (`ANALYST_DB_PASSWORD`,
  `GROQ_API_KEY`) and connects with the read-only role, never as the database owner.

## Known history

The v1 team project's history (Talend, April to May 2026) holds two real credentials that were committed back then
and are no longer in `main`: an ngrok auth token (`ngrok.yml`) and one Talend-encrypted database password (Talend
encrypts with a public default key, so treat it as readable). Both must be treated as burned: revoke the token in the
ngrok dashboard and change that password anywhere it is still used. `.gitleaks-baseline.json` records what history
already held so that CI fails on anything *new*; the other ~1,700 matches are generated hash keys and hostnames.

## Reporting a problem

Open a private security advisory on GitHub (Security tab of this repository) or write to
adriansalvadorekomo@outlook.com. Please do not open a public issue for a vulnerability.
