"""User-safe application exceptions."""


class InsightSQLError(Exception):
    """Base class for expected application errors."""


class ConfigurationError(InsightSQLError):
    """Application configuration is missing or invalid."""


class ModelProviderError(InsightSQLError):
    """The SQL generation provider could not return a usable response."""


class SQLValidationError(InsightSQLError):
    """Generated SQL is outside the permitted read-only query policy."""


class DatabaseError(InsightSQLError):
    """The read-only database could not execute a query."""


class QueryTimeoutError(DatabaseError):
    """The query exceeded its configured execution time."""
