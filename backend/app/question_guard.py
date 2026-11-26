"""The first control on a question: it must be a question, not code.

The analyst turns plain words into a query. If a visitor can type the query itself ("SELECT * FROM
marts.fact_reservation"), the model just passes it along and the analyst becomes a SQL console, so anything written
as SQL, a schema-qualified table, a catalog name or a comment is refused before it reaches the model. sql_guard,
the read-only transaction and the least-privilege role still sit behind this, so a miss here is not a breach.
"""

import re
import unicodedata

_STATEMENT_START = re.compile(
    r"^\W*(select\s*(\*|distinct\b|\d|\()|select\s+\w+\s*[,(]|with\s+\w+\s+as\s*\(|show\s+all\b|set\s+(role|session|local|"
    r"search_path)\b|(explain|copy|vacuum|grant|revoke|begin|commit|rollback|truncate|prepare|execute|listen|notify|"
    r"discard|reset)\b\s*[\w(;]*)", re.I)
_SQL_SHAPES = (
    re.compile(r"\bselect\b.{0,400}\bfrom\b", re.I | re.S),
    re.compile(r"\bunion\b\W+(all\W+)?select\b", re.I),
    re.compile(r"\b(insert\s+into|delete\s+from|drop\s+(table|schema|database|role|user|function|extension)|"
               r"alter\s+(table|role|user|system|database)|truncate\s+table|create\s+(table|function|role|user|"
               r"extension|schema)|update\s+\w+(\.\w+)?\s+set)\b", re.I),
    re.compile(r"\b(from|join)\s+\"?\w+\"?\s*\.\s*\"?\w+", re.I),
    re.compile(r"\b(marts|reporting|reference|quality|staging|raw|public|pg_catalog|information_schema)\s*\.\s*\w+",
               re.I),
    re.compile(r"\b(pg_\w+|information_schema|current_setting|set_config|lo_import|lo_export|dblink|copy\s+\w+\s+"
               r"(to|from)|analyst_ro|current_user|session_user|version\s*\(\))", re.I),
    re.compile(r";\s*(select|insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|set|with|call|do|begin|"
               r"commit|show|explain)\b", re.I),        # a second statement
    re.compile(r"--|/\*|\*/"),                   # SQL comments
    re.compile(r"\$\$|\$\w*\$"),                 # dollar quoting
    re.compile(r"('|\")\s*(or|and)\s+('|\"|\d)", re.I),    # ' or '1'='1
    re.compile(r"\b(or|and)\b\s+\d+\s*=\s*\d+", re.I),     # or 1=1
    re.compile(r"::\s*\w+"),                     # postgres cast
)


def looks_like_code(question: str) -> bool:
    text = unicodedata.normalize("NFKC", question)
    text = "".join(ch for ch in text if unicodedata.category(ch) not in ("Cf", "Cc") or ch in "\n\t ")
    text = re.sub(r"\s+", " ", text).strip()
    return bool(_STATEMENT_START.search(text)) or any(shape.search(text) for shape in _SQL_SHAPES)
