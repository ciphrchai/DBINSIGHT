import pytest

from insightsql.config import load_settings


def test_rejects_unsafe_row_limit(monkeypatch) -> None:
    monkeypatch.setenv("INSIGHTSQL_MAX_ROWS", "5001")

    with pytest.raises(ValueError, match="between 1 and 5000"):
        load_settings()


def test_loads_safe_defaults(monkeypatch) -> None:
    monkeypatch.delenv("INSIGHTSQL_MAX_ROWS", raising=False)
    monkeypatch.delenv("INSIGHTSQL_QUERY_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = load_settings()

    assert settings.max_rows == 500
    assert settings.query_timeout_seconds == 5
    assert settings.openai_api_key is None
