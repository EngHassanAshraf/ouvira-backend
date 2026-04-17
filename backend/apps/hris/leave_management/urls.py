from django.urls import path

# TODO: register leave management views here
from django.urls import path
from apps.hris.leave_management.api.views import (
    LeaveRequestListCreateView,
    LeaveRequestDetailView,
    LeaveCancelView,
    ManagerLeaveRequestListView,
    ManagerApproveView,
    HRApproveView,
    DeclineView,
    InterruptView,
    BulkApproveView,
    BulkDeclineView,
    EmployeeBalanceSummaryView,
    ManagerBalanceSummaryView,
    BalanceAdjustView,
    BalanceInitializeView,
)

app_name = "leave"

urlpatterns = [
    # --- Xodim: so'rovlar ---
    path("requests/", LeaveRequestListCreateView.as_view(), name="leave-list"),
    path("requests/<int:pk>/", LeaveRequestDetailView.as_view(), name="leave-detail"),
    path("requests/<int:pk>/cancel/", LeaveCancelView.as_view(), name="leave-cancel"),

    # --- Xodim: balans ---
    path("balance/", EmployeeBalanceSummaryView.as_view(), name="balance-summary"),

    # --- Menejer: so'rovlar ro'yxati ---
    path("manager/requests/", ManagerLeaveRequestListView.as_view(), name="manager-leave-list"),

    # --- Menejer: approve / decline ---
    path("manager/requests/<int:pk>/approve/", ManagerApproveView.as_view(), name="manager-approve"),
    path("manager/requests/<int:pk>/hr-approve/", HRApproveView.as_view(), name="hr-approve"),
    path("manager/requests/<int:pk>/decline/", DeclineView.as_view(), name="manager-decline"),
    path("manager/requests/<int:pk>/interrupt/", InterruptView.as_view(), name="manager-interrupt"),

    # --- Menejer: bulk ---
    path("manager/requests/bulk-approve/", BulkApproveView.as_view(), name="bulk-approve"),
    path("manager/requests/bulk-decline/", BulkDeclineView.as_view(), name="bulk-decline"),

    # --- Menejer: balans ---
    path("manager/employees/<int:employee_pk>/balance/", ManagerBalanceSummaryView.as_view(), name="manager-balance"),
    path("manager/employees/<int:employee_pk>/balance/adjust/", BalanceAdjustView.as_view(), name="balance-adjust"),
    path("manager/employees/<int:employee_pk>/balance/initialize/", BalanceInitializeView.as_view(), name="balance-initialize"),
]