from django.urls import path, include

app_name = "travel"

urlpatterns = [
    path("", include("apps.hris.travel_management.api.urls")),
]