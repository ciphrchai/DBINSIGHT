-- Employee management schema and sample data for Microsoft SQL Server.
-- Safe to rerun: schema objects are created only when absent, and seed rows
-- are matched by their unique department names, employee emails, and projects.

IF SCHEMA_ID(N'hr') IS NULL
    EXEC(N'CREATE SCHEMA hr');
GO

IF OBJECT_ID(N'hr.departments', N'U') IS NULL
BEGIN
    CREATE TABLE hr.departments
    (
        DepartmentID   int IDENTITY(1,1) NOT NULL,
        DepartmentName nvarchar(100) NOT NULL,
        Location       nvarchar(100) NOT NULL,
        Budget         decimal(14,2) NOT NULL,
        CreatedAt      datetime2(0) NOT NULL
            CONSTRAINT DF_departments_CreatedAt DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_departments PRIMARY KEY (DepartmentID),
        CONSTRAINT UQ_departments_DepartmentName UNIQUE (DepartmentName),
        CONSTRAINT CK_departments_Budget CHECK (Budget >= 0)
    );
END;
GO

IF OBJECT_ID(N'hr.employees', N'U') IS NULL
BEGIN
    CREATE TABLE hr.employees
    (
        EmployeeID   int IDENTITY(1,1) NOT NULL,
        DepartmentID int NOT NULL,
        FirstName    nvarchar(60) NOT NULL,
        LastName     nvarchar(60) NOT NULL,
        Email        nvarchar(254) NOT NULL,
        Phone        nvarchar(25) NULL,
        JobTitle     nvarchar(100) NOT NULL,
        HireDate     date NOT NULL,
        Salary       decimal(12,2) NOT NULL,
        IsActive     bit NOT NULL
            CONSTRAINT DF_employees_IsActive DEFAULT (1),
        CreatedAt    datetime2(0) NOT NULL
            CONSTRAINT DF_employees_CreatedAt DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_employees PRIMARY KEY (EmployeeID),
        CONSTRAINT UQ_employees_Email UNIQUE (Email),
        CONSTRAINT CK_employees_Salary CHECK (Salary >= 0),
        CONSTRAINT FK_employees_departments
            FOREIGN KEY (DepartmentID) REFERENCES hr.departments (DepartmentID)
    );
END;
GO

IF OBJECT_ID(N'hr.projects', N'U') IS NULL
BEGIN
    CREATE TABLE hr.projects
    (
        ProjectID   int IDENTITY(1,1) NOT NULL,
        ProjectName nvarchar(150) NOT NULL,
        Description nvarchar(500) NULL,
        StartDate   date NOT NULL,
        EndDate     date NULL,
        Budget      decimal(14,2) NOT NULL,
        Status      varchar(20) NOT NULL
            CONSTRAINT DF_projects_Status DEFAULT ('Planned'),
        CreatedAt   datetime2(0) NOT NULL
            CONSTRAINT DF_projects_CreatedAt DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_projects PRIMARY KEY (ProjectID),
        CONSTRAINT UQ_projects_ProjectName UNIQUE (ProjectName),
        CONSTRAINT CK_projects_Budget CHECK (Budget >= 0),
        CONSTRAINT CK_projects_Dates CHECK (EndDate IS NULL OR EndDate >= StartDate),
        CONSTRAINT CK_projects_Status
            CHECK (Status IN ('Planned', 'Active', 'On Hold', 'Completed', 'Cancelled'))
    );
END;
GO

IF OBJECT_ID(N'hr.employee_projects', N'U') IS NULL
BEGIN
    CREATE TABLE hr.employee_projects
    (
        EmployeeID       int NOT NULL,
        ProjectID        int NOT NULL,
        ProjectRole      nvarchar(100) NOT NULL,
        AssignedDate     date NOT NULL,
        AllocationPercent decimal(5,2) NOT NULL
            CONSTRAINT DF_employee_projects_AllocationPercent DEFAULT (100.00),
        CONSTRAINT PK_employee_projects PRIMARY KEY (EmployeeID, ProjectID),
        CONSTRAINT CK_employee_projects_AllocationPercent
            CHECK (AllocationPercent > 0 AND AllocationPercent <= 100),
        CONSTRAINT FK_employee_projects_employees
            FOREIGN KEY (EmployeeID) REFERENCES hr.employees (EmployeeID),
        CONSTRAINT FK_employee_projects_projects
            FOREIGN KEY (ProjectID) REFERENCES hr.projects (ProjectID)
    );
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'hr.employees')
      AND name = N'IX_employees_DepartmentID'
)
    CREATE INDEX IX_employees_DepartmentID ON hr.employees (DepartmentID);
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'hr.employee_projects')
      AND name = N'IX_employee_projects_ProjectID'
)
    CREATE INDEX IX_employee_projects_ProjectID
        ON hr.employee_projects (ProjectID, EmployeeID);
GO

SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    INSERT INTO hr.departments (DepartmentName, Location, Budget)
    SELECT seed.DepartmentName, seed.Location, seed.Budget
    FROM (VALUES
        (N'Engineering',        N'Bengaluru', 2500000.00),
        (N'Human Resources',    N'Bengaluru',  800000.00),
        (N'Finance',            N'Bengaluru', 1200000.00),
        (N'Sales',              N'Mumbai',    1800000.00),
        (N'Information Technology', N'Bengaluru', 1500000.00)
    ) AS seed (DepartmentName, Location, Budget)
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM hr.departments AS existing
        WHERE existing.DepartmentName = seed.DepartmentName
    );

    INSERT INTO hr.employees
        (DepartmentID, FirstName, LastName, Email, Phone, JobTitle, HireDate, Salary)
    SELECT department.DepartmentID, seed.FirstName, seed.LastName, seed.Email,
           seed.Phone, seed.JobTitle, seed.HireDate, seed.Salary
    FROM (VALUES
        (N'Aarav',  N'Sharma',  N'aarav.sharma@example.com',  N'+91-90000-00001', N'Software Engineer',    CONVERT(date, '2022-03-14'),  900000.00, N'Engineering'),
        (N'Ananya', N'Rao',     N'ananya.rao@example.com',    N'+91-90000-00002', N'Senior Engineer',      CONVERT(date, '2020-07-06'), 1450000.00, N'Engineering'),
        (N'Vikram', N'Patel',   N'vikram.patel@example.com',  N'+91-90000-00003', N'Data Engineer',        CONVERT(date, '2021-01-18'), 1150000.00, N'Engineering'),
        (N'Meera',  N'Iyer',    N'meera.iyer@example.com',    N'+91-90000-00004', N'Engineering Manager',  CONVERT(date, '2018-11-12'), 2100000.00, N'Engineering'),
        (N'Rohan',  N'Kapoor',  N'rohan.kapoor@example.com',  N'+91-90000-00005', N'HR Generalist',        CONVERT(date, '2021-06-21'),  750000.00, N'Human Resources'),
        (N'Priya',  N'Nair',    N'priya.nair@example.com',    N'+91-90000-00006', N'Talent Acquisition Lead', CONVERT(date, '2019-02-04'), 1100000.00, N'Human Resources'),
        (N'Karan',  N'Malhotra',N'karan.malhotra@example.com',N'+91-90000-00007', N'HR Coordinator',       CONVERT(date, '2023-08-01'),  620000.00, N'Human Resources'),
        (N'Sneha',  N'Das',     N'sneha.das@example.com',     N'+91-90000-00008', N'HR Manager',           CONVERT(date, '2017-05-15'), 1600000.00, N'Human Resources'),
        (N'Aditya', N'Kulkarni',N'aditya.kulkarni@example.com',N'+91-90000-00009',N'Financial Analyst',     CONVERT(date, '2022-09-19'),  850000.00, N'Finance'),
        (N'Kavya',  N'Menon',   N'kavya.menon@example.com',   N'+91-90000-00010', N'Senior Accountant',    CONVERT(date, '2020-04-13'), 1050000.00, N'Finance'),
        (N'Arjun',  N'Reddy',   N'arjun.reddy@example.com',   N'+91-90000-00011', N'Finance Manager',      CONVERT(date, '2016-10-03'), 1750000.00, N'Finance'),
        (N'Ishita', N'Joshi',   N'ishita.joshi@example.com',  N'+91-90000-00012', N'Payroll Specialist',   CONVERT(date, '2023-02-20'),  700000.00, N'Finance'),
        (N'Rahul',  N'Bose',    N'rahul.bose@example.com',    N'+91-90000-00013', N'Sales Executive',      CONVERT(date, '2022-01-10'),  800000.00, N'Sales'),
        (N'Pooja',  N'Singh',   N'pooja.singh@example.com',   N'+91-90000-00014', N'Account Manager',      CONVERT(date, '2020-08-17'), 1200000.00, N'Sales'),
        (N'Neil',   N'Fernandes',N'neil.fernandes@example.com',N'+91-90000-00015',N'Sales Analyst',        CONVERT(date, '2021-11-29'),  950000.00, N'Sales'),
        (N'Tanya',  N'Gupta',   N'tanya.gupta@example.com',   N'+91-90000-00016', N'Sales Manager',        CONVERT(date, '2018-03-26'), 1850000.00, N'Sales'),
        (N'Dev',    N'Chatterjee',N'dev.chatterjee@example.com',N'+91-90000-00017',N'System Administrator',CONVERT(date, '2021-04-05'), 1000000.00, N'Information Technology'),
        (N'Riya',   N'Krishnan',N'riya.krishnan@example.com', N'+91-90000-00018', N'Database Administrator', CONVERT(date, '2019-12-02'), 1400000.00, N'Information Technology'),
        (N'Sameer', N'Khan',    N'sameer.khan@example.com',   N'+91-90000-00019', N'IT Support Specialist',CONVERT(date, '2023-05-08'),  680000.00, N'Information Technology'),
        (N'Lavanya',N'Pillai',  N'lavanya.pillai@example.com',N'+91-90000-00020', N'IT Manager',           CONVERT(date, '2017-09-11'), 1700000.00, N'Information Technology')
    ) AS seed
        (FirstName, LastName, Email, Phone, JobTitle, HireDate, Salary, DepartmentName)
    INNER JOIN hr.departments AS department
        ON department.DepartmentName = seed.DepartmentName
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM hr.employees AS existing
        WHERE existing.Email = seed.Email
    );

    INSERT INTO hr.projects (ProjectName, Description, StartDate, EndDate, Budget, Status)
    SELECT seed.ProjectName, seed.Description, seed.StartDate, seed.EndDate,
           seed.Budget, seed.Status
    FROM (VALUES
        (N'Employee Portal',       N'Self-service portal for employee records and requests.', CONVERT(date, '2025-01-15'), CONVERT(date, '2025-09-30'), 1800000.00, 'Active'),
        (N'HRIS Modernization',    N'Modernize HR workflows and personnel data management.', CONVERT(date, '2025-02-01'), CONVERT(date, '2025-12-15'), 2200000.00, 'Active'),
        (N'Finance Automation',    N'Automate recurring finance and reconciliation processes.', CONVERT(date, '2025-03-01'), CONVERT(date, '2025-10-31'), 1400000.00, 'Active'),
        (N'Customer Data Platform',N'Consolidate customer data for reporting and analytics.', CONVERT(date, '2025-04-01'), NULL,                         3200000.00, 'Active'),
        (N'Cloud Migration',       N'Migrate selected internal services to a managed cloud platform.', CONVERT(date, '2025-01-06'), CONVERT(date, '2025-11-30'), 2800000.00, 'Active'),
        (N'Sales Analytics',       N'Provide sales teams with consistent pipeline and performance dashboards.', CONVERT(date, '2025-05-12'), CONVERT(date, '2025-10-15'),  950000.00, 'Planned'),
        (N'Security Improvement',  N'Improve access controls, monitoring, and security operations.', CONVERT(date, '2025-02-17'), CONVERT(date, '2025-08-29'), 1250000.00, 'Active'),
        (N'Learning Platform',     N'Roll out a learning platform for employee development.', CONVERT(date, '2025-06-02'), CONVERT(date, '2025-12-19'),  780000.00, 'Planned'),
        (N'Payroll Integration',   N'Integrate payroll processing with finance systems.', CONVERT(date, '2025-03-10'), CONVERT(date, '2025-09-12'), 1100000.00, 'Active'),
        (N'Infrastructure Refresh',N'Refresh core network and server infrastructure.', CONVERT(date, '2025-07-01'), NULL,                          2000000.00, 'Planned')
    ) AS seed (ProjectName, Description, StartDate, EndDate, Budget, Status)
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM hr.projects AS existing
        WHERE existing.ProjectName = seed.ProjectName
    );

    INSERT INTO hr.employee_projects
        (EmployeeID, ProjectID, ProjectRole, AssignedDate, AllocationPercent)
    SELECT employee.EmployeeID, project.ProjectID, seed.ProjectRole,
           seed.AssignedDate, seed.AllocationPercent
    FROM (VALUES
        (N'aarav.sharma@example.com',    N'Employee Portal',        N'Backend Developer',       CONVERT(date, '2025-01-15'), 50.00),
        (N'ananya.rao@example.com',      N'Employee Portal',        N'Tech Lead',               CONVERT(date, '2025-01-15'), 35.00),
        (N'priya.nair@example.com',      N'Employee Portal',        N'HR Product Owner',        CONVERT(date, '2025-01-20'), 20.00),
        (N'rohan.kapoor@example.com',    N'HRIS Modernization',     N'Business Analyst',        CONVERT(date, '2025-02-01'), 50.00),
        (N'meera.iyer@example.com',      N'HRIS Modernization',     N'Engineering Lead',        CONVERT(date, '2025-02-03'), 25.00),
        (N'sneha.das@example.com',       N'HRIS Modernization',     N'HR Sponsor',              CONVERT(date, '2025-02-05'), 15.00),
        (N'aditya.kulkarni@example.com', N'Finance Automation',     N'Finance Analyst',         CONVERT(date, '2025-03-01'), 40.00),
        (N'kavya.menon@example.com',     N'Finance Automation',     N'Process Lead',            CONVERT(date, '2025-03-03'), 30.00),
        (N'arjun.reddy@example.com',     N'Finance Automation',     N'Finance Sponsor',         CONVERT(date, '2025-03-05'), 15.00),
        (N'vikram.patel@example.com',    N'Customer Data Platform', N'Data Engineer',           CONVERT(date, '2025-04-01'), 50.00),
        (N'riya.krishnan@example.com',   N'Customer Data Platform', N'Database Administrator',  CONVERT(date, '2025-04-02'), 30.00),
        (N'neil.fernandes@example.com',  N'Customer Data Platform', N'Data Analyst',            CONVERT(date, '2025-04-04'), 20.00),
        (N'dev.chatterjee@example.com',  N'Cloud Migration',        N'Infrastructure Engineer', CONVERT(date, '2025-01-06'), 50.00),
        (N'lavanya.pillai@example.com',  N'Cloud Migration',        N'IT Project Sponsor',       CONVERT(date, '2025-01-06'), 15.00),
        (N'meera.iyer@example.com',      N'Cloud Migration',        N'Engineering Advisor',     CONVERT(date, '2025-01-10'), 10.00),
        (N'rahul.bose@example.com',      N'Sales Analytics',        N'Sales Representative',   CONVERT(date, '2025-05-12'), 30.00),
        (N'pooja.singh@example.com',     N'Sales Analytics',        N'Sales Product Owner',    CONVERT(date, '2025-05-12'), 25.00),
        (N'tanya.gupta@example.com',     N'Sales Analytics',        N'Sales Sponsor',          CONVERT(date, '2025-05-14'), 10.00),
        (N'sameer.khan@example.com',     N'Security Improvement',   N'Support Specialist',     CONVERT(date, '2025-02-17'), 35.00),
        (N'riya.krishnan@example.com',   N'Security Improvement',   N'Database Security Lead', CONVERT(date, '2025-02-18'), 20.00),
        (N'dev.chatterjee@example.com',  N'Security Improvement',   N'System Administrator',   CONVERT(date, '2025-02-19'), 25.00),
        (N'priya.nair@example.com',      N'Learning Platform',      N'Learning Lead',          CONVERT(date, '2025-06-02'), 25.00),
        (N'karan.malhotra@example.com',  N'Learning Platform',      N'HR Coordinator',         CONVERT(date, '2025-06-03'), 35.00),
        (N'aarav.sharma@example.com',    N'Learning Platform',      N'Integration Developer',  CONVERT(date, '2025-06-05'), 20.00),
        (N'ishita.joshi@example.com',    N'Payroll Integration',    N'Payroll Specialist',     CONVERT(date, '2025-03-10'), 40.00),
        (N'aditya.kulkarni@example.com', N'Payroll Integration',    N'Finance Analyst',        CONVERT(date, '2025-03-11'), 20.00),
        (N'vikram.patel@example.com',    N'Payroll Integration',    N'Data Integration Lead',  CONVERT(date, '2025-03-12'), 25.00),
        (N'lavanya.pillai@example.com',  N'Infrastructure Refresh', N'IT Project Manager',     CONVERT(date, '2025-07-01'), 30.00),
        (N'dev.chatterjee@example.com',  N'Infrastructure Refresh', N'System Administrator',   CONVERT(date, '2025-07-01'), 40.00),
        (N'sameer.khan@example.com',     N'Infrastructure Refresh', N'IT Support Specialist', CONVERT(date, '2025-07-03'), 25.00)
    ) AS seed (Email, ProjectName, ProjectRole, AssignedDate, AllocationPercent)
    INNER JOIN hr.employees AS employee
        ON employee.Email = seed.Email
    INNER JOIN hr.projects AS project
        ON project.ProjectName = seed.ProjectName
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM hr.employee_projects AS existing
        WHERE existing.EmployeeID = employee.EmployeeID
          AND existing.ProjectID = project.ProjectID
    );

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

-- Run this query to verify the minimum sample-data counts.
SELECT
    (SELECT COUNT(*) FROM hr.departments) AS DepartmentCount,
    (SELECT COUNT(*) FROM hr.employees) AS EmployeeCount,
    (SELECT COUNT(*) FROM hr.projects) AS ProjectCount,
    (SELECT COUNT(*) FROM hr.employee_projects) AS AssignmentCount;
GO
