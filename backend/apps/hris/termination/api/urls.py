"""
Termination Module API URLs / API URL Konfiguratsiyasi

URL patterns for all termination endpoints
Barcha tugatish endpointlari uchun URL patternlari
"""

from django.urls import path
from apps.hris.termination.api.views import *

# Total: 26 endpoints
urlpatterns = [
    # ========== EMPLOYEE ENDPOINTS (5) ==========
    # Xodim endpointlari

    # My resignation
    path(
        'my-resignation/',
        MyResignationView.as_view(),
        name='my-resignation'
    ),

    # Withdraw resignation
    path(
        'my-resignation/<int:resignation_id>/withdraw/',
        MyResignationWithdrawView.as_view(),
        name='my-resignation-withdraw'
    ),

    # My termination history
    path(
        'my-history/',
        MyTerminationHistoryView.as_view(),
        name='my-termination-history'
    ),

    # My termination detail
    path(
        'my-termination/<int:termination_id>/',
        MyTerminationDetailView.as_view(),
        name='my-termination-detail'
    ),

    # My warnings
    path(
        'my-warnings/',
        MyWarningsView.as_view(),
        name='my-warnings'
    ),

    # ========== HR/MANAGER ENDPOINTS (17) ==========
    # HR/Menejer endpointlari

    # --- Termination Management (6) ---

    # List all terminations
    path(
        'terminations/',
        TerminationListView.as_view(),
        name='termination-list'
    ),

    # Manager approve resignation
    path(
        'resignations/<int:resignation_id>/approve-manager/',
        ResignationApproveManagerView.as_view(),
        name='resignation-approve-manager'
    ),

    # GM approve resignation
    path(
        'resignations/<int:resignation_id>/approve-gm/',
        ResignationApproveGMView.as_view(),
        name='resignation-approve-gm'
    ),

    # Reject resignation
    path(
        'resignations/<int:resignation_id>/reject/',
        ResignationRejectView.as_view(),
        name='resignation-reject'
    ),

    # Initiate behavioral termination
    path(
        'terminations/behavioral/create/',
        BehavioralTerminationCreateView.as_view(),
        name='behavioral-termination-create'
    ),

    # Initiate performance termination
    path(
        'terminations/performance/create/',
        PerformanceTerminationCreateView.as_view(),
        name='performance-termination-create'
    ),

    # --- Warning Management (4) ---

    # List warnings
    path(
        'warnings/',
        WarningListView.as_view(),
        name='warning-list'
    ),

    # Issue absence warning
    path(
        'warnings/absence/create/',
        AbsenceWarningCreateView.as_view(),
        name='absence-warning-create'
    ),

    # Issue performance warning
    path(
        'warnings/performance/create/',
        PerformanceWarningCreateView.as_view(),
        name='performance-warning-create'
    ),

    # Escalate warning to termination
    path(
        'warnings/<int:warning_id>/escalate/',
        WarningEscalateView.as_view(),
        name='warning-escalate'
    ),

    # --- Settlement Management (4) ---

    # List settlements
    path(
        'settlements/',
        SettlementListView.as_view(),
        name='settlement-list'
    ),

    # Create settlement
    path(
        'settlements/create/',
        SettlementCreateView.as_view(),
        name='settlement-create'
    ),

    # Approve settlement
    path(
        'settlements/<int:settlement_id>/approve/',
        SettlementApproveView.as_view(),
        name='settlement-approve'
    ),

    # Process payment
    path(
        'settlements/<int:settlement_id>/payment/',
        SettlementPaymentView.as_view(),
        name='settlement-payment'
    ),

    # --- Exit Interview Management (3) ---

    # List exit interviews
    path(
        'exit-interviews/',
        ExitInterviewListView.as_view(),
        name='exit-interview-list'
    ),

    # Schedule exit interview
    path(
        'exit-interviews/schedule/',
        ExitInterviewScheduleView.as_view(),
        name='exit-interview-schedule'
    ),

    # Conduct exit interview
    path(
        'exit-interviews/<int:interview_id>/conduct/',
        ExitInterviewConductView.as_view(),
        name='exit-interview-conduct'
    ),

    # ========== REPORT ENDPOINTS (4) ==========
    # Hisobot endpointlari

    # Termination statistics
    path(
        'reports/statistics/',
        TerminationStatisticsView.as_view(),
        name='termination-statistics'
    ),

    # Exit interview insights
    path(
        'reports/exit-interview-insights/',
        ExitInterviewInsightsView.as_view(),
        name='exit-interview-insights'
    ),

    # Settlement summary
    path(
        'reports/settlement-summary/',
        SettlementSummaryView.as_view(),
        name='settlement-summary'
    ),

    # Pending approvals
    path(
        'reports/pending-approvals/',
        PendingApprovalsView.as_view(),
        name='pending-approvals'
    ),
]