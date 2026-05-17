from django.urls import path
from apps.hris.travel_management.api.views import (
    # Employee
    BusinessTripRequestListCreateView,
    BusinessTripRequestDetailView,
    BusinessTripRequestCancelView,
    MyBusinessTripBalanceView,
    # Manager
    ManagerBusinessTripRequestListView,
    ManagerApproveView,
    HRApproveView,
    DeclineView,
    InterruptView,
    BulkApproveView,
    BulkDeclineView,
    # Balance
    BusinessTripBalanceListView,
    BusinessTripBalanceDetailView,
    BusinessTripBalanceAdjustView,
    BusinessTripBulkAdjustView,
    BusinessTripCSVImportView,
    BusinessTripCSVTemplateView,
    BusinessTripAdjustmentLogView,
)

urlpatterns = [
    # Employee endpoints
    path("requests/", BusinessTripRequestListCreateView.as_view(), name="trip-request-list-create"),
    path("requests/<int:pk>/", BusinessTripRequestDetailView.as_view(), name="trip-request-detail"),
    path("requests/<int:pk>/cancel/", BusinessTripRequestCancelView.as_view(), name="trip-request-cancel"),
    path("balance/my/", MyBusinessTripBalanceView.as_view(), name="my-trip-balance"),

    # Manager endpoints
    path("requests/all/", ManagerBusinessTripRequestListView.as_view(), name="manager-trip-request-list"),
    path("requests/<int:pk>/manager-approve/", ManagerApproveView.as_view(), name="manager-approve"),
    path("requests/<int:pk>/hr-approve/", HRApproveView.as_view(), name="hr-approve"),
    path("requests/<int:pk>/decline/", DeclineView.as_view(), name="decline"),
    path("requests/<int:pk>/interrupt/", InterruptView.as_view(), name="interrupt"),
    path("requests/bulk-approve/", BulkApproveView.as_view(), name="bulk-approve"),
    path("requests/bulk-decline/", BulkDeclineView.as_view(), name="bulk-decline"),

    # Balance management (HR)
    path("balance/", BusinessTripBalanceListView.as_view(), name="balance-list"),
    path("balance/<int:pk>/", BusinessTripBalanceDetailView.as_view(), name="balance-detail"),
    path("balance/<int:pk>/adjust/", BusinessTripBalanceAdjustView.as_view(), name="balance-adjust"),
    path("balance/bulk-adjust/", BusinessTripBulkAdjustView.as_view(), name="balance-bulk-adjust"),
    path("balance/import/", BusinessTripCSVImportView.as_view(), name="balance-import"),
    path("balance/import/template/", BusinessTripCSVTemplateView.as_view(), name="balance-template"),
    path("balance/active-log/", BusinessTripAdjustmentLogView.as_view(), name="balance-active-log"),
]