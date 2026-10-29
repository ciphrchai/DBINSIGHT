"""Deterministic, key-free SQL generation for common employee questions."""

from __future__ import annotations

import re

from insightsql.errors import ModelProviderError

OFFLINE_EXAMPLES = (
    "How many employees are there?",
    "Show employees by department.",
    "List all employees.",
    "List all departments.",
    "List all projects.",
    "Show project assignment counts.",
)


def generate_offline_sql(question: str) -> str:
    """Map supported question patterns to fixed, read-only SQL templates."""
    normalized = re.sub(r"[^a-z0-9 ]+", " ", question.casefold())
    words = set(normalized.split())
    has_employee = bool(words & {"employee", "employees", "staff"})
    has_department = bool(words & {"department", "departments"})
    has_project = bool(words & {"project", "projects"})

    if has_employee and has_department and (
        words & {"count", "counts", "many", "number", "group"}
    ):
        return (
            "SELECT d.DepartmentName, COUNT(e.EmployeeID) AS EmployeeCount "
            "FROM departments AS d "
            "LEFT JOIN employees AS e ON e.DepartmentID = d.DepartmentID "
            "GROUP BY d.DepartmentID, d.DepartmentName "
            "ORDER BY d.DepartmentName"
        )

    if words & {"assignment", "assignments", "staffing"} and (
        words & {"count", "counts", "many", "number"} or has_project
    ):
        return (
            "SELECT p.ProjectName, COUNT(ep.EmployeeID) AS AssignmentCount "
            "FROM projects AS p "
            "LEFT JOIN employee_projects AS ep ON ep.ProjectID = p.ProjectID "
            "GROUP BY p.ProjectID, p.ProjectName "
            "ORDER BY p.ProjectName"
        )

    if has_employee and words & {"list", "show", "all", "details"}:
        return (
            "SELECT EmployeeID, FirstName, LastName, JobTitle, Email, DepartmentID "
            "FROM employees ORDER BY LastName, FirstName"
        )

    if has_employee and words & {"count", "counts", "many", "number", "total"}:
        return "SELECT COUNT(*) AS EmployeeCount FROM employees"

    if has_department and words & {"list", "show", "all", "details"}:
        return (
            "SELECT DepartmentID, DepartmentName, Location, Budget "
            "FROM departments ORDER BY DepartmentName"
        )

    if has_project and words & {"list", "show", "all", "details"}:
        return (
            "SELECT ProjectID, ProjectName, StartDate, EndDate, Budget, Status "
            "FROM projects ORDER BY ProjectName"
        )

    supported = "; ".join(OFFLINE_EXAMPLES)
    raise ModelProviderError(
        "Offline mode is active because no OpenAI API key is configured. "
        f"This question does not match a supported query yet. Try: {supported}"
    )
