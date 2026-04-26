from django.urls import path
from apps.hris.leave_management.api.views import (
    # Employee views
    LeaveRequestListCreateView,
    LeaveRequestDetailView,
    LeaveCancelView,
    # Manager views
    ManagerLeaveRequestListView,
    ManagerApproveView,
    HRApproveView,
    DeclineView,
    InterruptView,
    BulkApproveView,
    BulkDeclineView,
    # Balance views
    EmployeeBalanceSummaryView,
    ManagerBalanceSummaryView,
    BalanceAdjustView,
    BalanceInitializeView,
    LeaveActivityLogListAPIView,

    LeavePDFExportView,
    ManagerLeavePDFExportView,
    LeaveBalanceAdjustmentLogView,
    LeaveBalanceCSVImportView,
)
from leave_management.api.views.balance_import_view import LeaveBalanceCSVTemplateView

app_name = "leave"

urlpatterns = [
    # ── Employee endpoints ─────────────────────────────────────────────────────
    path("leave-requests/", LeaveRequestListCreateView.as_view(), name="leave-request-list"),
    path("leave-requests/<int:pk>/", LeaveRequestDetailView.as_view(), name="leave-request-detail"),
    path("leave-requests/<int:pk>/cancel/", LeaveCancelView.as_view(), name="leave-request-cancel"),

    # ── Manager endpoints ──────────────────────────────────────────────────────
    path("manager/leave-requests/", ManagerLeaveRequestListView.as_view(), name="manager-leave-list"),
    path("manager/leave-requests/<int:pk>/approve/", ManagerApproveView.as_view(), name="manager-approve"),
    path("manager/leave-requests/<int:pk>/hr-approve/", HRApproveView.as_view(), name="hr-approve"),
    path("manager/leave-requests/<int:pk>/decline/", DeclineView.as_view(), name="decline"),
    path("manager/leave-requests/<int:pk>/interrupt/", InterruptView.as_view(), name="interrupt"),
    path("manager/leave-requests/bulk-approve/", BulkApproveView.as_view(), name="bulk-approve"),
    path("manager/leave-requests/bulk-decline/", BulkDeclineView.as_view(), name="bulk-decline"),
    path("activity-logs/", LeaveActivityLogListAPIView.as_view(), name="activity-logs"),

    # ── Balance endpoints ──────────────────────────────────────────────────────
    path("balance/", EmployeeBalanceSummaryView.as_view(), name="balance-summary"),
    path("balance/manager/<int:employee_pk>/", ManagerBalanceSummaryView.as_view()),
    path("balance/adjust/<int:employee_pk>/", BalanceAdjustView.as_view()),
    path("balance/initialize/<int:employee_pk>/", BalanceInitializeView.as_view()),

    # ── PDF Export endpoints ───────────────────────────────────────────────────
    path("leave-requests/<int:pk>/export-pdf/", LeavePDFExportView.as_view(), name="leave-export-pdf"),
    path("manager/leave-requests/<int:pk>/export-pdf/", ManagerLeavePDFExportView.as_view(), name="manager-leave-export-pdf"),
    path("balance/adjustment-log/",LeaveBalanceAdjustmentLogView.as_view(),name="leave-balance-adjustment-log"),
    path("balance/import-csv/", LeaveBalanceCSVImportView.as_view(), name="leave-balance-import-csv"),
    path("balance/import-csv/template/",LeaveBalanceCSVTemplateView.as_view(),name="leave-balance-csv-template"
),
]