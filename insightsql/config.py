"""Validated application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    database_path: Path
    openai_api_key: str | None
    openai_model: str
    max_rows: int
    query_timeout_seconds: int


def load_settings() -> Settings:
    """Load settings and fail explicitly for unsafe or invalid limits."""
    database_value = os.getenv("INSIGHTSQL_DATABASE_PATH", "employee_management.db")
    database_path = Path(database_value).expanduser()
    if not database_path.is_absolute():
        database_path = PROJECT_ROOT / database_path

    try:
        max_rows = int(os.getenv("INSIGHTSQL_MAX_ROWS", "500"))
        timeout = int(os.getenv("INSIGHTSQL_QUERY_TIMEOUT_SECONDS", "5"))
    except ValueError as exc:
        raise ValueError("INSIGHTSQL_MAX_ROWS and INSIGHTSQL_QUERY_TIMEOUT_SECONDS must be integers.") from exc

    if not 1 <= max_rows <= 5000:
        raise ValueError("INSIGHTSQL_MAX_ROWS must be between 1 and 5000.")
    if not 1 <= timeout <= 60:
        raise ValueError("INSIGHTSQL_QUERY_TIMEOUT_SECONDS must be between 1 and 60.")

    api_key = os.getenv("OPENAI_API_KEY", "").strip() or None
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    if not model:
        raise ValueError("OPENAI_MODEL cannot be empty.")

    return Settings(
        database_path=database_path.resolve(),
        openai_api_key=api_key,
        openai_model=model,
        max_rows=max_rows,
        query_timeout_seconds=timeout,
    )
