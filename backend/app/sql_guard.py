"""The hard control on model-written SQL: one read-only SELECT on the analytics schemas, with a row limit.

The database role behind it (analyst_ro) is read-only too; this guard rejects anything else before it is sent.
"""

import sqlglot
from sqlglot import exp

ALLOWED_SCHEMAS = {"marts", "reporting", "reference", "quality"}
FORBIDDEN_FUNCTIONS = {"pg_sleep", "pg_read_file", "pg_read_binary_file", "pg_ls_dir", "dblink", "lo_import",
                       "lo_export", "set_config", "current_setting", "pg_terminate_backend", "pg_cancel_backend"}
MAX_ROWS = 200


class UnsafeSQL(ValueError):
    """The SQL was rejected; the message says why and is safe to show."""


def guard(sql: str) -> str:
    """Return a safe version of `sql` (row limit enforced) or raise UnsafeSQL."""
    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except sqlglot.errors.ParseError as error:
        raise UnsafeSQL("the query could not be parsed") from error
    if len(statements) != 1:
        raise UnsafeSQL("exactly one statement is allowed")
    tree = statements[0]
    if not isinstance(tree, exp.Query):
        raise UnsafeSQL("only SELECT queries are allowed")
    for node in tree.walk():
        if isinstance(node, (exp.Insert, exp.Update, exp.Delete, exp.Merge, exp.Create, exp.Drop, exp.Alter,
                             exp.Command, exp.Into)):
            raise UnsafeSQL("only SELECT queries are allowed")
        if isinstance(node, exp.Func) and node.sql_name().lower() in FORBIDDEN_FUNCTIONS:
            raise UnsafeSQL(f"function {node.sql_name().lower()} is not allowed")
        if isinstance(node, exp.Anonymous) and str(node.this).lower() in FORBIDDEN_FUNCTIONS:
            raise UnsafeSQL(f"function {str(node.this).lower()} is not allowed")
    ctes = {cte.alias_or_name for cte in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        if table.name in ctes and not table.db:
            continue
        if table.db not in ALLOWED_SCHEMAS:
            raise UnsafeSQL(f"table {table.sql()} is outside the analytics schemas")
    limit = tree.args.get("limit")
    if limit is None or int(limit.expression.name) > MAX_ROWS:
        tree = tree.limit(MAX_ROWS)
    return tree.sql(dialect="postgres")
