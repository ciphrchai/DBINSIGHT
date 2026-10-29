import sqlite3
from pathlib import Path

import pytest

from insightsql.database import execute_readonly
from insightsql.errors import DatabaseError


def test_executes_select_and_returns_column_names(test_database) -> None:
    columns, rows, truncated = execute_readonly(
        test_database, "SELECT FirstName, Salary FROM employees"
    )

    assert columns == ["FirstName", "Salary"]
    assert rows == [("Aarav", 900000)]
    assert not truncated


def test_limits_returned_rows(test_database) -> None:
    columns, rows, truncated = execute_readonly(
        test_database,
        "SELECT EmployeeID FROM employees UNION ALL SELECT EmployeeID FROM employees",
        max_rows=1,
    )

    assert columns == ["EmployeeID"]
    assert len(rows) == 1
    assert truncated


def test_readonly_connection_does_not_allow_writes(test_database) -> None:
    with pytest.raises(DatabaseError):
        execute_readonly(
            test_database,
            "INSERT INTO employees VALUES (2, 1, 'Test', 'User', 'test@example.com', 1)",
        )

    connection = sqlite3.connect(test_database)
    try:
        assert connection.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 1
    finally:
        connection.close()


def test_reports_missing_database() -> None:
    with pytest.raises(DatabaseError, match="configured database file"):
        execute_readonly(Path("missing.db"), "SELECT 1")
