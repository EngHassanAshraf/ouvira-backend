from django.urls import path

from .views import CompanyListCreateView, CompanyDetailView, CompanySettingsView

app_name = "company"

urlpatterns = [
    path("", CompanyListCreateView.as_view(), name="company-list"),
    path("<int:pk>/", CompanyDetailView.as_view(), name="company-detail"),
    path("<int:pk>/settings/", CompanySettingsView.as_view(), name="company-settings"),
]
