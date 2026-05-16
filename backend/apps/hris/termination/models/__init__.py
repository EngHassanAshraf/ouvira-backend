"""
Termination Module Models

Exports:
- TerminationRequest: Main model for resignations and all termination types
- TerminationWarning: Absence and performance warnings
- ExitInterview: Exit interview records
- TerminationSettlement: Final settlement calculations
"""

from .termination_request import TerminationRequest
from .termination_warning import TerminationWarning
from .exit_interview import ExitInterview
from .termination_settlement import TerminationSettlement

__all__ = [
    "TerminationRequest",
    "TerminationWarning",
    "ExitInterview",
    "TerminationSettlement",
]
