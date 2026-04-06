from django.urls import path
from apps.hris.hris_core.api.views import (
    EmployeeListCreateApiView, EmployeeDetailApiView, PositionListCreateApiView,
    PositionDetailApiView, AttendanceListCreateApiView, AttendanceDetailApiView,
    JobTitleListCreateApiView, JobTitleDetailApiView, LocationListCreateApiView,
    LocationDetailApiView, DepartmentListCreateApiView, DepartmentDetailApiView,
    EmploymentListCreateApiView, EmploymentDetailApiView,

)


urlpatterns = [
    path('locations/', LocationListCreateApiView.as_view(), name='location-list-create'),
    path('employees/', EmployeeListCreateApiView.as_view(), name='employee-list-create'),
    path('employees/<int:pk>/', EmployeeDetailApiView.as_view(), name='employee-detail'),

    path("locations/<int:pk>/", LocationDetailApiView.as_view(), name="location-detail"),

    path("departments/", DepartmentListCreateApiView.as_view(), name="department-list-create"),
    path("departments/<int:pk>/", DepartmentDetailApiView.as_view(), name="department-detail"),

    path("job-titles/", JobTitleListCreateApiView.as_view(), name="jobtitle-list-create"),
    path("job-titles/<int:pk>/", JobTitleDetailApiView.as_view(), name="jobtitle-detail"),

    path("employees/<int:employee_pk>/employments/", EmploymentListCreateApiView.as_view(), name="employment-list-create"),
    path("employees/<int:employee_pk>/employments/<int:pk>/", EmploymentDetailApiView.as_view(), name="employment-detail"),

    path("positions/", PositionListCreateApiView.as_view(), name="position-list-create"),
    path("positions/<int:pk>/", PositionDetailApiView.as_view(), name="position-detail"),

    path("employees/<int:employee_pk>/attendances/", AttendanceListCreateApiView.as_view(), name="attendance-list-create"),
    path("employees/<int:employee_pk>/attendances/<int:pk>/", AttendanceDetailApiView.as_view(), name="attendance-detail"),
]