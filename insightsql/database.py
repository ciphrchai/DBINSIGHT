"""Bounded read-only SQLite query execution."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

from insightsql.errors import DatabaseError, QueryTimeoutError


def execute_readonly(
    database_path: Path,
    sql: str,
    *,
    max_rows: int = 500,
    timeout_seconds: int = 5,
) -> tuple[list[str], list[tuple[Any, ...]], bool]:
    """Execute a query against an existing SQLite file without write access."""
    if not database_path.is_file():
        raise DatabaseError(
            "The configured database file was not found. Check INSIGHTSQL_DATABASE_PATH."
        )
    if not 1 <= max_rows <= 5000:
        raise ValueError("max_rows must be between 1 and 5000.")
    if not 1 <= timeout_seconds <= 60:
        raise ValueError("timeout_seconds must be between 1 and 60.")

    uri = f"{database_path.resolve().as_uri()}?mode=ro"
    deadline = time.monotonic() + timeout_seconds
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=timeout_seconds)
        connection.execute("PRAGMA query_only = ON")
        connection.set_progress_handler(
            lambda: int(time.monotonic() > deadline),
            1000,
        )
        cursor = connection.execute(sql)
        columns = [description[0] for description in cursor.description or ()]
        rows = cursor.fetchmany(max_rows + 1)
        return columns, rows[:max_rows], len(rows) > max_rows
    except sqlite3.OperationalError as exc:
        if "interrupted" in str(exc).casefold() and time.monotonic() > deadline:
            raise QueryTimeoutError(
                f"Query exceeded the {timeout_seconds}-second limit."
            ) from exc
        raise DatabaseError("The query could not be run against the database.") from exc
    except sqlite3.Error as exc:
        raise DatabaseError("The database could not complete the query.") from exc
    finally:
        if connection is not None:
            connection.close()
