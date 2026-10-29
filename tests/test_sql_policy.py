import pytest

from insightsql.errors import SQLValidationError
from insightsql.sql_policy import validate_select


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM employees",
        "select DepartmentName from departments;",
        "WITH staff AS (SELECT * FROM employees) SELECT * FROM staff",
        "SELECT * FROM employees UNION SELECT * FROM employees",
    ],
)
def test_allows_select_queries_over_allowed_tables(sql: str) -> None:
    assert validate_select(sql).upper().startswith(("SELECT", "WITH"))


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "UPDATE employees SET Salary = 0",
        "DELETE FROM employees",
        "INSERT INTO employees VALUES (1, 1, 'A', 'B', 'a@b.c', 1)",
        "DROP TABLE employees",
        "TRUNCATE TABLE employees",
        "ALTER TABLE employees ADD COLUMN secret TEXT",
        "SELECT * FROM employees; DELETE FROM employees",
        "SELECT * FROM sqlite_master",
        "SELECT * FROM main.employees",
        "SELECT SecretField FROM employees",
        "SELECT load_extension('extension')",
    ],
)
def test_rejects_non_select_multiple_or_unauthorized_sql(sql: str) -> None:
    with pytest.raises(SQLValidationError):
        validate_select(sql)
