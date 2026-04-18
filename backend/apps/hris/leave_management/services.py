import logging
from django.db import transaction
from django.utils import timezone

from apps.hris.leave_management.models import LeaveType, LeaveRequest

logger = logging.getLogger(__name__)


class LeaveTypeService:

    @staticmethod
    @transaction.atomic
    def create_leave_type(**data) -> LeaveType:
        leave_type = LeaveType.objects.create(**data)
        logger.info("LeaveType created: %s", leave_type.name)
        return leave_type

    @staticmethod
    @transaction.atomic
    def update_leave_type(leave_type_id: int, **data) -> LeaveType:
        lt = LeaveType.objects.filter(id=leave_type_id, is_deleted=False).first()
        if not lt:
            raise ValueError("Leave type not found")
        for attr, value in data.items():
            setattr(lt, attr, value)
        lt.save()
        return lt

    @staticmethod
    @transaction.atomic
    def delete_leave_type(leave_type_id: int) -> None:
        lt = LeaveType.objects.filter(id=leave_type_id, is_deleted=False).first()
        if not lt:
            raise ValueError("Leave type not found")
        lt.is_deleted = True
        lt.deleted_at = timezone.now()
        lt.save(update_fields=["is_deleted", "deleted_at"])


class LeaveRequestService:

    @staticmethod
    @transaction.atomic
    def create_request(employee_id: int, **data) -> LeaveRequest:
        # Prevent duplicate pending/approved requests for the same period
        start = data.get("start_date")
        end = data.get("end_date")
        if start and end and start > end:
            raise ValueError("start_date must be before end_date")

        req = LeaveRequest.objects.create(
            employee_id=employee_id,
            status=LeaveRequest.StatusChoice.PENDING,
            **data,
        )
        logger.info("LeaveRequest created: pk=%s employee=%s", req.pk, employee_id)
        return req

    @staticmethod
    @transaction.atomic
    def update_request(request_id: int, employee_id: int, **data) -> LeaveRequest:
        req = LeaveRequest.objects.filter(
            id=request_id, employee_id=employee_id, is_deleted=False
        ).first()
        if not req:
            raise ValueError("Leave request not found")
        if req.status != LeaveRequest.StatusChoice.PENDING:
            raise ValueError("Only pending requests can be edited")
        for attr, value in data.items():
            setattr(req, attr, value)
        req.save()
        return req

    @staticmethod
    @transaction.atomic
    def approve_request(request_id: int, approver_employee_id: int) -> LeaveRequest:
        req = LeaveRequest.objects.filter(
            id=request_id, is_deleted=False
        ).first()
        if not req:
            raise ValueError("Leave request not found")
        if req.status != LeaveRequest.StatusChoice.PENDING:
            raise ValueError("Only pending requests can be approved")
        req.status = LeaveRequest.StatusChoice.APPROVED
        req.approved_by_id = approver_employee_id
        req.save(update_fields=["status", "approved_by_id"])
        logger.info("LeaveRequest approved: pk=%s by=%s", request_id, approver_employee_id)
        return req

    @staticmethod
    @transaction.atomic
    def reject_request(request_id: int, approver_employee_id: int) -> LeaveRequest:
        req = LeaveRequest.objects.filter(
            id=request_id, is_deleted=False
        ).first()
        if not req:
            raise ValueError("Leave request not found")
        if req.status != LeaveRequest.StatusChoice.PENDING:
            raise ValueError("Only pending requests can be rejected")
        req.status = LeaveRequest.StatusChoice.REJECTED
        req.approved_by_id = approver_employee_id
        req.save(update_fields=["status", "approved_by_id"])
        logger.info("LeaveRequest rejected: pk=%s by=%s", request_id, approver_employee_id)
        return req

    @staticmethod
    @transaction.atomic
    def cancel_request(request_id: int, employee_id: int) -> LeaveRequest:
        req = LeaveRequest.objects.filter(
            id=request_id, employee_id=employee_id, is_deleted=False
        ).first()
        if not req:
            raise ValueError("Leave request not found")
        if req.status not in (
            LeaveRequest.StatusChoice.PENDING,
            LeaveRequest.StatusChoice.APPROVED,
        ):
            raise ValueError("Only pending or approved requests can be cancelled")
        req.is_deleted = True
        req.deleted_at = timezone.now()
        req.save(update_fields=["is_deleted", "deleted_at"])
        logger.info("LeaveRequest cancelled: pk=%s", request_id)
        return req
