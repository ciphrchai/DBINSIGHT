"""Parsing and enforcement for the application's read-only SQL policy."""

from __future__ import annotations

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from insightsql.errors import SQLValidationError
from insightsql.schema import ALLOWED_COLUMNS, ALLOWED_TABLES


def validate_select(sql: str, allowed_tables: frozenset[str] = ALLOWED_TABLES) -> str:
    """Return normalized SQL only when it is a single SELECT on allowed tables."""
    if not isinstance(sql, str) or not sql.strip():
        raise SQLValidationError("The SQL generator returned an empty query.")
    if len(sql) > 10_000:
        raise SQLValidationError("The generated SQL is too long to run safely.")

    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except ParseError as exc:
        raise SQLValidationError("The generated SQL could not be parsed safely.") from exc

    if len(statements) != 1 or statements[0] is None:
        raise SQLValidationError("Only one SQL statement can be run at a time.")

    statement = statements[0]
    if not isinstance(statement, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        raise SQLValidationError("Only read-only SELECT queries are allowed.")

    cte_names = {
        cte.alias_or_name.casefold()
        for cte in statement.find_all(exp.CTE)
        if cte.alias_or_name
    }
    query_aliases = {
        alias.alias.casefold()
        for alias in statement.find_all(exp.Alias)
        if alias.alias
    }
    for cte in statement.find_all(exp.CTE):
        cte_alias = cte.args.get("alias")
        if cte_alias:
            query_aliases.update(
                identifier.name.casefold()
                for identifier in (cte_alias.args.get("columns") or [])
            )

    for table in statement.find_all(exp.Table):
        name = table.name.casefold()
        if name not in allowed_tables and name not in cte_names:
            raise SQLValidationError("The query references a table that is not allowed.")
        if table.db or table.catalog:
            raise SQLValidationError("Qualified or attached databases are not allowed.")

    for column in statement.find_all(exp.Column):
        name = column.name.casefold()
        if name != "*" and name not in ALLOWED_COLUMNS and name not in query_aliases:
            raise SQLValidationError("The query references a column that is not allowed.")

    for node in statement.walk():
        if isinstance(node, exp.Anonymous):
            function_name = node.name.casefold()
            if function_name in {"load_extension", "readfile", "writefile"}:
                raise SQLValidationError("This SQL function is not allowed.")

    return statement.sql(dialect="sqlite")
