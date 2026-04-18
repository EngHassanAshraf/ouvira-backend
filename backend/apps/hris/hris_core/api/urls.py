from django.urls import path

from apps.hris.hris_core.api.views import (
    # Location
    LocationListCreateApiView,
    LocationDetailApiView,
    # Department
    DepartmentListCreateApiView,
    DepartmentDetailApiView,
    # Job Title
    JobTitleListCreateApiView,
    JobTitleDetailApiView,
    # Position
    PositionListCreateApiView,
    PositionDetailApiView,
    # Employee — CRUD
    EmployeeListCreateApiView,
    EmployeeDetailApiView,
    EmployeeArchiveListApiView,
    EmployeeRestoreApiView,
    # Employee — Bulk / Import / Export
    EmployeeBulkArchiveApiView,
    EmployeeBulkRestoreApiView,
    EmployeeImportApiView,
    EmployeeExportApiView,
    # Employee — Full create (single payload)
    EmployeeFullCreateApiView,
    # Employment
    EmploymentListCreateApiView,
    EmploymentDetailApiView,
    # Leave Balance
    EmployeeLeaveBalanceListCreateApiView,
    EmployeeLeaveBalanceDetailApiView,
    # Allowance
    EmployeeAllowanceListCreateApiView,
    EmployeeAllowanceDetailApiView,
    # Bank Detail
    EmployeeBankDetailApiView,
    # Cost
    EmployeeCostListCreateApiView,
    EmployeeCostDetailApiView,
    # Document
    EmployeeDocumentListCreateApiView,
    EmployeeDocumentDetailApiView,
    # Attendance
    AttendanceListCreateApiView,
    AttendanceDetailApiView,
)

app_name = "hris-core"

urlpatterns = [
    # ── Locations ──────────────────────────────────────────────────────────────
    path("locations/", LocationListCreateApiView.as_view(), name="location-list"),
    path("locations/<int:pk>/", LocationDetailApiView.as_view(), name="location-detail"),

    # ── Departments ────────────────────────────────────────────────────────────
    path("departments/", DepartmentListCreateApiView.as_view(), name="department-list"),
    path("departments/<int:pk>/", DepartmentDetailApiView.as_view(), name="department-detail"),

    # ── Job Titles ─────────────────────────────────────────────────────────────
    path("job-titles/", JobTitleListCreateApiView.as_view(), name="job-title-list"),
    path("job-titles/<int:pk>/", JobTitleDetailApiView.as_view(), name="job-title-detail"),

    # ── Positions ──────────────────────────────────────────────────────────────
    path("positions/", PositionListCreateApiView.as_view(), name="position-list"),
    path("positions/<int:pk>/", PositionDetailApiView.as_view(), name="position-detail"),

    # ── Employees — CRUD ───────────────────────────────────────────────────────
    # NOTE: fixed-string paths must come before <int:pk> paths
    path("employees/archived/",     EmployeeArchiveListApiView.as_view(),  name="employee-archived"),
    path("employees/bulk-archive/", EmployeeBulkArchiveApiView.as_view(),  name="employee-bulk-archive"),
    path("employees/bulk-restore/", EmployeeBulkRestoreApiView.as_view(),  name="employee-bulk-restore"),
    path("employees/import/",       EmployeeImportApiView.as_view(),       name="employee-import"),
    path("employees/export/",       EmployeeExportApiView.as_view(),       name="employee-export"),
    path("employees/full/",         EmployeeFullCreateApiView.as_view(),   name="employee-full-create"),
    path("employees/",              EmployeeListCreateApiView.as_view(),    name="employee-list"),
    path("employees/<int:pk>/",     EmployeeDetailApiView.as_view(),       name="employee-detail"),
    path("employees/<int:pk>/restore/", EmployeeRestoreApiView.as_view(),  name="employee-restore"),

    # ── Employments (nested) ───────────────────────────────────────────────────
    path("employees/<int:employee_pk>/employments/",
         EmploymentListCreateApiView.as_view(), name="employment-list"),
    path("employees/<int:employee_pk>/employments/<int:pk>/",
         EmploymentDetailApiView.as_view(), name="employment-detail"),

    # ── Leave Balances (nested) ────────────────────────────────────────────────
    path("employees/<int:employee_pk>/leave-balances/",
         EmployeeLeaveBalanceListCreateApiView.as_view(), name="leave-balance-list"),
    path("employees/<int:employee_pk>/leave-balances/<int:pk>/",
         EmployeeLeaveBalanceDetailApiView.as_view(), name="leave-balance-detail"),

    # ── Allowances (nested) ────────────────────────────────────────────────────
    path("employees/<int:employee_pk>/allowances/",
         EmployeeAllowanceListCreateApiView.as_view(), name="allowance-list"),
    path("employees/<int:employee_pk>/allowances/<int:pk>/",
         EmployeeAllowanceDetailApiView.as_view(), name="allowance-detail"),

    # ── Bank Detail (singleton nested) ────────────────────────────────────────
    path("employees/<int:employee_pk>/bank-detail/",
         EmployeeBankDetailApiView.as_view(), name="bank-detail"),

    # ── Costs (nested) ─────────────────────────────────────────────────────────
    path("employees/<int:employee_pk>/costs/",
         EmployeeCostListCreateApiView.as_view(), name="cost-list"),
    path("employees/<int:employee_pk>/costs/<int:pk>/",
         EmployeeCostDetailApiView.as_view(), name="cost-detail"),

    # ── Documents (nested) ────────────────────────────────────────────────────
    path("employees/<int:employee_pk>/documents/",
         EmployeeDocumentListCreateApiView.as_view(), name="document-list"),
    path("employees/<int:employee_pk>/documents/<int:pk>/",
         EmployeeDocumentDetailApiView.as_view(), name="document-detail"),

    # ── Attendance (nested) ────────────────────────────────────────────────────
    path("employees/<int:employee_pk>/attendances/",
         AttendanceListCreateApiView.as_view(), name="attendance-list"),
    path("employees/<int:employee_pk>/attendances/<int:pk>/",
         AttendanceDetailApiView.as_view(), name="attendance-detail"),
]
