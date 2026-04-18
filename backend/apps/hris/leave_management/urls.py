from django.urls import path
from apps.hris.leave_management.views import (
    LeaveTypeListCreateApiView,
    LeaveTypeDetailApiView,
    LeaveRequestListCreateApiView,
    LeaveRequestDetailApiView,
    LeaveRequestCancelApiView,
    LeaveRequestApproveApiView,
    LeaveRequestRejectApiView,
)

app_name = "leave"

urlpatterns = [
    # ── Leave Types ────────────────────────────────────────────────────────────
    path("leave-types/",          LeaveTypeListCreateApiView.as_view(), name="leave-type-list"),
    path("leave-types/<int:pk>/", LeaveTypeDetailApiView.as_view(),     name="leave-type-detail"),

    # ── Leave Requests — fixed paths before <int:pk> ───────────────────────────
    path("leave-requests/",               LeaveRequestListCreateApiView.as_view(), name="leave-request-list"),
    path("leave-requests/<int:pk>/",      LeaveRequestDetailApiView.as_view(),     name="leave-request-detail"),
    path("leave-requests/<int:pk>/cancel/",  LeaveRequestCancelApiView.as_view(),  name="leave-request-cancel"),
    path("leave-requests/<int:pk>/approve/", LeaveRequestApproveApiView.as_view(), name="leave-request-approve"),
    path("leave-requests/<int:pk>/reject/",  LeaveRequestRejectApiView.as_view(),  name="leave-request-reject"),
]
