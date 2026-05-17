"""
HRIS URL aggregator
====================
All HRIS sub-module routes are collected here and mounted under /api/v1/hris/
by the root urls.py.

  core/           → employees, departments, locations, positions, attendance
  recruitment/    → hiring requests, job ads, candidates, interviews, offers
  leave/          → leave requests & balances
  expense/        → expense claims & approvals
  travel/         → travel requests & itineraries
  performance/    → reviews, goals, KPIs
  analytics/      → workforce analytics & reports
  termination/    → offboarding & termination records
"""

from django.urls import include, path

app_name = "hris"

urlpatterns = [
    path("core/",        include("apps.hris.hris_core.api.urls",                    namespace="hris-core")),
    path("recruitment/", include("apps.hris.recruitment.infrastructure.api.urls",   namespace="recruitment")),
    path("expense/",     include("apps.hris.expense_management.urls",               namespace="expense")),
    path("travel/",      include("apps.hris.travel_management.urls",                namespace="travel")),
    path("performance/", include("apps.hris.performance.urls",                      namespace="performance")),
    path("analytics/",   include("apps.hris.analytics.urls",                        namespace="analytics")),
    path("leave/",       include("apps.hris.leave_management.api.urls",             namespace="leave")),
    # Internal company authentication (separate from external/tenant auth)
    path("internal/auth/", include("apps.hris.internal_auth.api.urls",             namespace="internal_auth")),
]
