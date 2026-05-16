"""
Termination Module Views

Exports all API views for termination management
"""

# Employee Views
from .employee_views import (
    MyResignationView,
    MyResignationWithdrawView,
    MyTerminationHistoryView,
    MyTerminationDetailView,
    MyWarningsView,
)

# HR Views
from .hr_views import (
    TerminationListView,
    ResignationApproveManagerView,
    ResignationApproveGMView,
    ResignationRejectView,
    BehavioralTerminationCreateView,
    PerformanceTerminationCreateView,
    WarningListView,
    AbsenceWarningCreateView,
    PerformanceWarningCreateView,
    WarningEscalateView,
    SettlementListView,
    SettlementCreateView,
    SettlementApproveView,
    SettlementPaymentView,
    ExitInterviewListView,
    ExitInterviewScheduleView,
    ExitInterviewConductView,
)

# Report Views
from .report_views import (
    TerminationStatisticsView,
    ExitInterviewInsightsView,
    SettlementSummaryView,
    PendingApprovalsView,
)

__all__ = [
    # Employee (5)
    "MyResignationView",
    "MyResignationWithdrawView",
    "MyTerminationHistoryView",
    "MyTerminationDetailView",
    "MyWarningsView",
    # HR (17)
    "TerminationListView",
    "ResignationApproveManagerView",
    "ResignationApproveGMView",
    "ResignationRejectView",
    "BehavioralTerminationCreateView",
    "PerformanceTerminationCreateView",
    "WarningListView",
    "AbsenceWarningCreateView",
    "PerformanceWarningCreateView",
    "WarningEscalateView",
    "SettlementListView",
    "SettlementCreateView",
    "SettlementApproveView",
    "SettlementPaymentView",
    "ExitInterviewListView",
    "ExitInterviewScheduleView",
    "ExitInterviewConductView",
    # Reports (4)
    "TerminationStatisticsView",
    "ExitInterviewInsightsView",
    "SettlementSummaryView",
    "PendingApprovalsView",
]