"""
Termination Module URLs
"""

from django.urls import path, include

# IMPORTANT: app_name is required for namespace in include()
app_name = "termination"

# API v1 URLs
urlpatterns = [
    path("", include("apps.hris.termination.api.urls")),
]