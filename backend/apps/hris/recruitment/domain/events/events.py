from dataclasses import dataclass
from uuid import UUID
from .dispatcher import DomainEvent

@dataclass
class HiringRequestEvent(DomainEvent):
    request_id: int
    company_id: int

@dataclass
class HiringRequestSubmitted(HiringRequestEvent):
    submitted_by_id: int

@dataclass
class HiringRequestApproved(HiringRequestEvent):
    approved_by_id: int

@dataclass
class HiringRequestRejected(HiringRequestEvent):
    rejected_by_id: int
    reason: str
