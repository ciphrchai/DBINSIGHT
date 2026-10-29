import pytest

from insightsql.errors import ModelProviderError
from insightsql.llm import generate_sql
from insightsql.offline_queries import generate_offline_sql


@pytest.mark.parametrize(
    ("question", "expected_table"),
    [
        ("How many employees are there?", "FROM employees"),
        ("Show employee counts by department", "FROM departments AS d"),
        ("List all employees", "FROM employees"),
        ("Show all departments", "FROM departments"),
        ("List all projects", "FROM projects"),
        ("Show project assignment counts", "FROM projects AS p"),
    ],
)
def test_offline_mode_generates_supported_queries(
    question: str, expected_table: str
) -> None:
    sql = generate_sql(question, api_key=None, model="unused-without-key")

    assert expected_table in sql
    assert sql.lstrip().upper().startswith("SELECT")


def test_offline_mode_rejects_unsupported_questions() -> None:
    with pytest.raises(ModelProviderError, match="Offline mode is active"):
        generate_offline_sql("Find employees hired last year in Mumbai")
