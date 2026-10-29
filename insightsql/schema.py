"""Allowlisted schema context provided to the SQL generator."""

SCHEMA_CONTEXT = """SQLite database tables:

departments(DepartmentID, DepartmentName, Location, Budget, CreatedAt)
employees(EmployeeID, DepartmentID, FirstName, LastName, Email, Phone,
          JobTitle, HireDate, Salary, IsActive, CreatedAt)
projects(ProjectID, ProjectName, Description, StartDate, EndDate, Budget,
         Status, CreatedAt)
employee_projects(EmployeeID, ProjectID, ProjectRole, AssignedDate,
                  AllocationPercent)

Relationships:
- employees.DepartmentID references departments.DepartmentID
- employee_projects.EmployeeID references employees.EmployeeID
- employee_projects.ProjectID references projects.ProjectID

Return one SQLite SELECT statement only. Never return markdown, explanations,
write statements, PRAGMA, or more than one statement. Use only these tables
and columns. Prefer explicit column names and sensible LIMIT clauses."""

ALLOWED_TABLES = frozenset(
    {"departments", "employees", "projects", "employee_projects"}
)

ALLOWED_COLUMNS = frozenset(
    {
        "departmentid",
        "departmentname",
        "location",
        "budget",
        "createdat",
        "employeeid",
        "firstname",
        "lastname",
        "email",
        "phone",
        "jobtitle",
        "hiredate",
        "salary",
        "isactive",
        "projectid",
        "description",
        "startdate",
        "enddate",
        "status",
        "projectrole",
        "assigneddate",
        "allocationpercent",
    }
)
