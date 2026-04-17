from django.urls import path
from apps.hris.travel_management.views import (
    TravelRequestListCreateApiView,
    TravelRequestDetailApiView,
)

app_name = "travel"

urlpatterns = [
    path("travel-requests/",          TravelRequestListCreateApiView.as_view(), name="travel-request-list"),
    path("travel-requests/<int:pk>/",  TravelRequestDetailApiView.as_view(),    name="travel-request-detail"),
]
