"""Streamlit entry point for insightSQL."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

import pandas as pd
import streamlit as st

from insightsql.config import load_settings
from insightsql.database import execute_readonly
from insightsql.errors import (
    DatabaseError,
    ModelProviderError,
    SQLValidationError,
)
from insightsql.llm import generate_sql
from insightsql.sql_policy import validate_select

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("insightsql")

st.set_page_config(page_title="insightSQL", page_icon="🔎", layout="wide")

st.title("insightSQL")
st.caption("Ask questions about your employee, department, and project data.")

try:
    settings = load_settings()
except ValueError as exc:
    st.error(f"Configuration issue: {exc}")
    st.stop()

if not settings.database_path.is_file():
    st.error(
        "The SQLite database was not found. Set INSIGHTSQL_DATABASE_PATH in your local .env file."
    )
    st.stop()

st.caption(f"Database: `{settings.database_path.name}` · Read-only SQL execution")
if settings.openai_api_key:
    st.caption(f"SQL generation: OpenAI model `{settings.openai_model}`")
else:
    st.info(
        "Offline mode: no OpenAI key is needed for common questions. "
        "Try counting employees, listing employees/departments/projects, "
        "counting employees by department, or counting project assignments."
    )

if "query_history" not in st.session_state:
    st.session_state.query_history = []

with st.form("question_form"):
    question = st.text_area(
        "Ask a question",
        placeholder="For example: Show the number of employees in each department.",
        max_chars=1000,
        height=100,
    )
    submitted = st.form_submit_button("Generate SQL", type="primary")

if submitted:
    normalized_question = question.strip()
    if not normalized_question:
        st.warning("Enter a question to generate a query.")
    else:
        st.session_state.pop("pending_query", None)
        st.session_state.pop("latest_result", None)
        request_id = str(uuid.uuid4())
        try:
            with st.spinner("Generating a SQL query..."):
                candidate = generate_sql(
                    normalized_question,
                    api_key=settings.openai_api_key,
                    model=settings.openai_model,
                )
                approved_sql = validate_select(candidate)
            st.session_state.pending_query = {
                "request_id": request_id,
                "question": normalized_question,
                "sql": approved_sql,
            }
            logger.info("sql_generated request_id=%s", request_id)
        except ModelProviderError as exc:
            logger.warning("generation_failed request_id=%s", request_id)
            st.error(str(exc))
        except SQLValidationError as exc:
            logger.warning("sql_rejected request_id=%s", request_id)
            st.error(f"The generated query was blocked: {exc}")
        except Exception:
            logger.exception("unexpected_generation_error request_id=%s", request_id)
            st.error(
                f"An unexpected error occurred. Try again; reference ID: {request_id}"
            )

pending_query = st.session_state.get("pending_query")
if pending_query:
    st.subheader("Generated SQL")
    st.code(pending_query["sql"], language="sql")
    st.caption("Review the query before running it. Only validated SELECT queries are accepted.")

    if st.button("Run this query", type="primary", key="run_query"):
        try:
            approved_sql = validate_select(pending_query["sql"])
            columns, rows, truncated = execute_readonly(
                settings.database_path,
                approved_sql,
                max_rows=settings.max_rows,
                timeout_seconds=settings.query_timeout_seconds,
            )
            result = pd.DataFrame.from_records(rows, columns=columns)
            st.session_state.latest_result = result
            st.session_state.query_history.insert(
                0,
                {
                    "time": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "question": pending_query["question"],
                    "sql": approved_sql,
                    "row_count": len(rows),
                },
            )
            del st.session_state.query_history[20:]
            logger.info(
                "query_succeeded request_id=%s row_count=%d",
                pending_query["request_id"],
                len(rows),
            )
            if truncated:
                st.info(f"Showing up to {settings.max_rows} rows.")
        except DatabaseError as exc:
            logger.warning(
                "query_failed request_id=%s error_type=%s",
                pending_query["request_id"],
                type(exc).__name__,
            )
            st.error(str(exc))
        except Exception:
            logger.exception(
                "unexpected_execution_error request_id=%s",
                pending_query["request_id"],
            )
            st.error(
                "The query could not be completed. Check the database and try again. "
                f"Reference ID: {pending_query['request_id']}"
            )

latest_result = st.session_state.get("latest_result")
if latest_result is not None:
    st.subheader("Query results")
    st.dataframe(latest_result, use_container_width=True, hide_index=True)
    st.download_button(
        "Download results as CSV",
        data=latest_result.to_csv(index=False).encode("utf-8"),
        file_name="insightsql-results.csv",
        mime="text/csv",
    )

history = st.session_state.query_history
if history:
    st.subheader("Query history")
    for index, item in enumerate(history):
        label = f"{item['time']} · {item['question'][:80]}"
        with st.expander(label):
            st.caption(f"Returned {item['row_count']} row(s)")
            st.code(item["sql"], language="sql")
            if st.button("Load query for review", key=f"history_{index}"):
                st.session_state.pending_query = {
                    "request_id": str(uuid.uuid4()),
                    "question": item["question"],
                    "sql": item["sql"],
                }
                st.rerun()
