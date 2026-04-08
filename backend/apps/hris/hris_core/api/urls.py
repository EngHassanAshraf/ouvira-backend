from django.urls import path

from apps.hris.hris_core.api.views import (
    LocationListCreateApiView,
    LocationDetailApiView,
    DepartmentListCreateApiView,
    DepartmentDetailApiView,
    JobTitleListCreateApiView,
    JobTitleDetailApiView,
    PositionListCreateApiView,
    PositionDetailApiView,
    EmployeeListCreateApiView,
    EmployeeDetailApiView,
    EmploymentListCreateApiView,
    EmploymentDetailApiView,
    AttendanceListCreateApiView,
    AttendanceDetailApiView,
)

app_name = "hris-core"

urlpatterns = [
    # --- Locations ---
    path("locations/", LocationListCreateApiView.as_view(), name="location-list"),
    path("locations/<int:pk>/", LocationDetailApiView.as_view(), name="location-detail"),

    # --- Departments ---
    path("departments/", DepartmentListCreateApiView.as_view(), name="department-list"),
    path("departments/<int:pk>/", DepartmentDetailApiView.as_view(), name="department-detail"),

    # --- Job titles ---
    path("job-titles/", JobTitleListCreateApiView.as_view(), name="job-title-list"),
    path("job-titles/<int:pk>/", JobTitleDetailApiView.as_view(), name="job-title-detail"),

    # --- Positions ---
    path("positions/", PositionListCreateApiView.as_view(), name="position-list"),
    path("positions/<int:pk>/", PositionDetailApiView.as_view(), name="position-detail"),

    # --- Employees ---
    path("employees/", EmployeeListCreateApiView.as_view(), name="employee-list"),
    path("employees/<int:pk>/", EmployeeDetailApiView.as_view(), name="employee-detail"),

    # --- Employments (nested under employee) ---
    path("employees/<int:employee_pk>/employments/", EmploymentListCreateApiView.as_view(), name="employment-list"),
    path("employees/<int:employee_pk>/employments/<int:pk>/", EmploymentDetailApiView.as_view(), name="employment-detail"),

    # --- Attendance (nested under employee) ---
    path("employees/<int:employee_pk>/attendances/", AttendanceListCreateApiView.as_view(), name="attendance-list"),
    path("employees/<int:employee_pk>/attendances/<int:pk>/", AttendanceDetailApiView.as_view(), name="attendance-detail"),
]