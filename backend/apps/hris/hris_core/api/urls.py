from django.urls import path
from apps.hris.hris_core.api.views import LocationListCreateApiView, EmployeeListCreateApiView

urlpatterns = [
    path('locations/', LocationListCreateApiView.as_view(), name='location-list-create'),
    path('employees/', EmployeeListCreateApiView.as_view(), name='employee-list-create'),
]