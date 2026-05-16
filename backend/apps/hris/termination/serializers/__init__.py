"""
Termination Module Serializers

Exports all serializers for API endpoints
"""

# Termination Request Serializers
from .termination_request_serializers import (
    TerminationRequestListSerializer,
    TerminationRequestDetailSerializer,
    ResignationCreateSerializer,
    ResignationWithdrawSerializer,
    TerminationApprovalSerializer,
    TerminationRejectionSerializer,
    BehavioralTerminationCreateSerializer,
    PerformanceTerminationCreateSerializer,
    ProbationTerminationCreateSerializer,
    MedicalTerminationCreateSerializer,
    LayoffCreateSerializer,
    DeceasedEmployeeSerializer,
)

# Warning Serializers
from .termination_warning_serializers import (
    TerminationWarningListSerializer,
    TerminationWarningDetailSerializer,
    AbsenceWarningCreateSerializer,
    PerformanceWarningCreateSerializer,
    WarningAcknowledgeSerializer,
    WarningResolveSerializer,
    WarningEscalateSerializer,
)

# Settlement Serializers
from .settlement_serializers import (
    TerminationSettlementListSerializer,
    TerminationSettlementDetailSerializer,
    SettlementCreateSerializer,
    SettlementAdjustSerializer,
    SettlementPaymentSerializer,
)

# Exit Interview Serializers
from .exit_interview_serializers import (
    ExitInterviewListSerializer,
    ExitInterviewDetailSerializer,
    ExitInterviewScheduleSerializer,
    ExitInterviewConductSerializer,
    ExitInterviewRescheduleSerializer,
    ExitInterviewCancelSerializer,
    ExitInterviewNoShowSerializer,
)

__all__ = [
    # Termination Request (12)
    "TerminationRequestListSerializer",
    "TerminationRequestDetailSerializer",
    "ResignationCreateSerializer",
    "ResignationWithdrawSerializer",
    "TerminationApprovalSerializer",
    "TerminationRejectionSerializer",
    "BehavioralTerminationCreateSerializer",
    "PerformanceTerminationCreateSerializer",
    "ProbationTerminationCreateSerializer",
    "MedicalTerminationCreateSerializer",
    "LayoffCreateSerializer",
    "DeceasedEmployeeSerializer",
    # Warning (7)
    "TerminationWarningListSerializer",
    "TerminationWarningDetailSerializer",
    "AbsenceWarningCreateSerializer",
    "PerformanceWarningCreateSerializer",
    "WarningAcknowledgeSerializer",
    "WarningResolveSerializer",
    "WarningEscalateSerializer",
    # Settlement (5)
    "TerminationSettlementListSerializer",
    "TerminationSettlementDetailSerializer",
    "SettlementCreateSerializer",
    "SettlementAdjustSerializer",
    "SettlementPaymentSerializer",
    # Exit Interview (7)
    "ExitInterviewListSerializer",
    "ExitInterviewDetailSerializer",
    "ExitInterviewScheduleSerializer",
    "ExitInterviewConductSerializer",
    "ExitInterviewRescheduleSerializer",
    "ExitInterviewCancelSerializer",
    "ExitInterviewNoShowSerializer",
]