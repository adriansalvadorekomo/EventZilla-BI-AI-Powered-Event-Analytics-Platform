"""The hard control on model-written SQL: one read-only SELECT on a fixed set of analytics tables.

Everything here is an ALLOW-LIST. The earlier version blocked a list of dangerous function names, which is the wrong
shape: an attacker needs one name that is not on the list ("set_config" in quotes, pg_sleep_for, query_to_xml, which
runs a string the guard never parses) and the control is gone. Now a query is accepted only if every function,
table, data type and construct in it is known to be safe, and it stays within size and shape limits that keep one
question from becoming a denial of service.

The query that runs is the one regenerated from the parsed tree, never the text that was received, so a difference
between this parser and PostgreSQL's cannot smuggle anything through. Two more layers sit behind this one: the
database role (analyst_ro: read-only, SELECT on the analytics schemas only) and the transaction that runs the query
(db.run_readonly: read-only, short timeouts).
"""

import sqlglot
from sqlglot import exp

# the tables the analyst may read: exactly what the semantic layer describes
ALLOWED_TABLES: dict[str, frozenset[str]] = {
    "marts": frozenset({"fact_reservation", "dim_date", "dim_event", "dim_service", "dim_provider",
                        "dim_beneficiary", "dim_geography"}),
    "reporting": frozenset({"rpt_marketing_monthly", "rpt_site_traffic_daily", "rpt_complaint_summary"}),
    "reference": frozenset({"ref_platform_review", "ref_location", "ref_competitor"}),
    "quality": frozenset({"rejected_evaluations", "rejected_marketing_months", "flagged_reservation_dates",
                          "flagged_traffic_days"}),
}

# every function a question may use. Names are sqlglot's: typed functions by sql_name (date_trunc is
# timestamp_trunc, to_char is time_to_str), others by their own name. Nothing that can sleep, read files or the
# catalog, run a string as SQL, hold locks, change settings or sequences, build huge values (repeat, lpad,
# generate_series) or run a regular expression (ReDoS) is here.
ALLOWED_FUNCTIONS = frozenset({
    # aggregates
    "count", "sum", "avg", "min", "max", "corr", "median", "stddev", "stddev_pop", "stddev_samp", "variance",
    "var_pop", "var_samp", "percentile_cont", "percentile_disc", "regr_slope", "regr_intercept", "regr_r2",
    # logic (sqlglot classes the operators AND / OR / EXISTS as functions)
    "and", "or", "xor", "exists",
    # scalar
    "round", "abs", "ceil", "ceiling", "floor", "trunc", "sqrt", "power", "pow", "ln", "log", "sign", "mod",
    "greatest", "least", "coalesce", "nullif", "case", "if", "cast", "extract", "lower", "upper", "length",
    "substring", "trim", "concat", "split_part",
    # dates
    "timestamp_trunc", "date_trunc", "time_to_str", "to_char", "date_part", "current_date", "current_timestamp",
    "date_diff", "datediff", "date_add", "date_sub",
    # windows
    "row_number", "rank", "dense_rank", "ntile", "lag", "lead", "first_value", "last_value", "nth_value",
    "percent_rank", "cume_dist",
})

ALLOWED_TYPES = frozenset({"INT", "BIGINT", "SMALLINT", "DECIMAL", "DOUBLE", "FLOAT", "REAL", "TEXT", "VARCHAR",
                           "CHAR", "DATE", "TIMESTAMP", "TIMESTAMPTZ", "BOOLEAN", "INTERVAL"})

# constructs that have no place in an analytical SELECT
FORBIDDEN_NODES = (
    exp.Insert, exp.Update, exp.Delete, exp.Merge, exp.Create, exp.Drop, exp.Alter, exp.Command, exp.Into, exp.Lock,
    exp.Dot,                                  # schema.function(...) and field access
    exp.Lateral, exp.Unnest, exp.Values,      # table functions and literal row sets
    exp.Parameter, exp.Placeholder, exp.SessionParameter,
    exp.RegexpLike, exp.RegexpILike, exp.SimilarTo,
)

MAX_ROWS = 200
MAX_OFFSET = 10_000
MAX_SQL_CHARS = 4_000
MAX_NODES = 1_200
MAX_JOINS = 8
MAX_SELECTS = 12


class UnsafeSQL(ValueError):
    """The SQL was rejected; the message says why and is safe to show."""


def _function_name(node: exp.Func) -> str:
    return node.name.lower() if isinstance(node, exp.Anonymous) else node.sql_name().lower()


def guard(sql: str) -> str:
    """Return a safe version of `sql` (row limit enforced) or raise UnsafeSQL. Fails closed on anything unexpected."""
    try:
        return _guard(sql)
    except UnsafeSQL:
        raise
    except Exception as error:  # a parser or generator bug must refuse the query, never let it through or crash
        raise UnsafeSQL("the query could not be checked") from error


def _guard(sql: str) -> str:
    if not isinstance(sql, str) or not sql.strip():
        raise UnsafeSQL("the query is empty")
    if len(sql) > MAX_SQL_CHARS:
        raise UnsafeSQL("the query is too long")
    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except sqlglot.errors.SqlglotError as error:
        raise UnsafeSQL("the query could not be parsed") from error
    except RecursionError as error:
        raise UnsafeSQL("the query is too complex") from error
    if len(statements) != 1:
        raise UnsafeSQL("exactly one statement is allowed")
    tree = statements[0]
    if not isinstance(tree, exp.Query):
        raise UnsafeSQL("only SELECT queries are allowed")

    ctes = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    nodes = selects = joins = 0
    for node in tree.walk():
        nodes += 1
        if nodes > MAX_NODES:
            raise UnsafeSQL("the query is too complex")
        if isinstance(node, FORBIDDEN_NODES):
            raise UnsafeSQL("only SELECT queries are allowed" if isinstance(
                node, (exp.Insert, exp.Update, exp.Delete, exp.Merge, exp.Create, exp.Drop, exp.Alter, exp.Command,
                       exp.Into)) else f"{type(node).__name__.lower()} is not allowed")
        if isinstance(node, exp.Func):
            name = _function_name(node)
            if name not in ALLOWED_FUNCTIONS:
                raise UnsafeSQL(f"function {name} is not allowed")
        elif isinstance(node, exp.DataType):
            kind = node.this.name if isinstance(node.this, exp.DataType.Type) else ""
            if kind not in ALLOWED_TYPES:
                raise UnsafeSQL(f"type {node.sql(dialect='postgres')} is not allowed")
        elif isinstance(node, exp.With) and node.args.get("recursive"):
            raise UnsafeSQL("recursive queries are not allowed")
        elif isinstance(node, exp.Join):
            joins += 1
            if joins > MAX_JOINS:
                raise UnsafeSQL("too many joins")
            if not (node.args.get("on") or node.args.get("using")):
                raise UnsafeSQL("every join needs an ON or USING condition")
        elif isinstance(node, exp.Select):
            selects += 1
            if selects > MAX_SELECTS:
                raise UnsafeSQL("the query is too complex")
        elif isinstance(node, exp.Table):
            _check_table(node, ctes)

    _bound_rows(tree)
    # comments dropped: text an attacker controls must not travel into the query that runs
    return tree.sql(dialect="postgres", comments=False)


def _check_table(table: exp.Table, ctes: set[str]) -> None:
    if not isinstance(table.this, exp.Identifier):
        raise UnsafeSQL("table functions are not allowed")
    schema, name = table.db.lower(), table.name.lower()
    if not schema and name in ctes:
        return
    if table.catalog or schema not in ALLOWED_TABLES:
        raise UnsafeSQL(f"table {table.sql()} is outside the analytics schemas")
    if name not in ALLOWED_TABLES[schema]:
        raise UnsafeSQL(f"table {table.sql()} is not one the analyst can read")


def _bound_rows(tree: exp.Query) -> None:
    """At most MAX_ROWS rows, whatever form the LIMIT takes (none, ALL, an expression, FETCH FIRST...)."""
    limit = tree.args.get("limit")
    count = None
    if isinstance(limit, exp.Limit) and isinstance(limit.expression, exp.Literal) and not limit.expression.is_string:
        try:
            count = int(limit.expression.name)
        except ValueError:
            count = None
    if count is None or count > MAX_ROWS:
        tree.set("limit", None)
        tree.limit(MAX_ROWS, copy=False)
    offset = tree.args.get("offset")
    if offset is not None:
        value = offset.expression
        if not (isinstance(value, exp.Literal) and not value.is_string and int(value.name) <= MAX_OFFSET):
            raise UnsafeSQL("OFFSET must be a small number")
