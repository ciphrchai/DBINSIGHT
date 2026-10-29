from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def test_database(tmp_path: Path) -> Path:
    database_path = tmp_path / "test.db"
    connection = sqlite3.connect(database_path)
    connection.executescript(
        """
        CREATE TABLE departments (
            DepartmentID INTEGER PRIMARY KEY,
            DepartmentName TEXT NOT NULL,
            Location TEXT NOT NULL,
            Budget NUMERIC NOT NULL
        );
        CREATE TABLE employees (
            EmployeeID INTEGER PRIMARY KEY,
            DepartmentID INTEGER NOT NULL,
            FirstName TEXT NOT NULL,
            LastName TEXT NOT NULL,
            Email TEXT NOT NULL,
            Salary NUMERIC NOT NULL,
            FOREIGN KEY (DepartmentID) REFERENCES departments (DepartmentID)
        );
        INSERT INTO departments VALUES (1, 'Engineering', 'Bengaluru', 250000);
        INSERT INTO employees VALUES (1, 1, 'Aarav', 'Sharma', 'aarav@example.com', 900000);
        """
    )
    connection.commit()
    connection.close()
    return database_path
