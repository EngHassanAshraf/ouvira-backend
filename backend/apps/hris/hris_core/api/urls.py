from django.urls import path
from apps.hris.hris_core.api.views import (
    LocationListCreateApiView,
    EmployeeListCreateApiView,
    EmployeeDetailApiView,
    LocationListCreateApiView,
    LocationDetailApiView,
)
from apps.hris.hris_core.api.views import (
    LocationListCreateApiView,
    LocationDetailApiView,
    DepartmentListCreateApiView,
    DepartmentDetailApiView,

)

urlpatterns = [
    path('locations/', LocationListCreateApiView.as_view(), name='location-list-create'),
    path('employees/', EmployeeListCreateApiView.as_view(), name='employee-list-create'),
    path('employees/<int:pk>/', EmployeeDetailApiView.as_view(), name='employee-detail'),

    path("locations/<int:pk>/", LocationDetailApiView.as_view(), name="location-detail"),

    path("departments/", DepartmentListCreateApiView.as_view(), name="department-list-create"),
    path("departments/<int:pk>/", DepartmentDetailApiView.as_view(), name="department-detail"),
]