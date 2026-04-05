import logging

from django.core.management.commands import check
from django.db import transaction
from apps.hris.hris_core.models.attendance import AttendanceRecord

logger = logging.getLogger(__name__)


class AttendanceService:

    @staticmethod
    @transaction.atomic
    def check_in(employee_id: int, date, check_in_time)-> AttendanceRecord:
        attendance, created = AttendanceRecord.objects.get_or_create(
            employee_id=employee_id,
            date=date,
            defaults={
                "check_in_time": check_in_time,
                "status": AttendanceRecord.StatusChoice.PRESENT,
            }
        )
        if not created:
            raise ValueError("Attendance record already exists for this data.")
        logger.info(f"Check-in: employee_id={employee_id}, date={date}")
        return attendance

    @staticmethod
    @transaction.atomic
    def check_out(employee_id: int, date, check_out_time)-> AttendanceRecord:
        attendance = AttendanceRecord.objects.filter(
            employee_id=employee_id, date=date, is_deleted=False
        ).first()

        if not attendance:
            raise ValueError("Attendance record not found.")

        attendance.check_out_time = check_out_time
        attendance.save()
        logger.info(f"Check-out: employee_id={employee_id}, date={date}")
        return attendance



    @staticmethod
    @transaction.atomic
    def update_attendance(attendance_id: int, employee_id: int, **data)-> AttendanceRecord:
        attendance = AttendanceRecord.objects.filter(
            id=attendance_id, employee_id=employee_id, is_deleted=False
        ).first()

        if not attendance:
            raise ValueError("Attendance record not found.")

        for attr, value in data.items():
            setattr(attendance, attr, value)

        attendance.save()
        return attendance


    @staticmethod
    @transaction.atomic
    def delete_attendance(attendance_id: int, employee_id: int)-> None:
        attendance = AttendanceRecord.objects.filter(
            id=attendance_id, employee_id=employee_id, is_deleted=False
        ).first()

        if not attendance:
            raise ValueError("Attendance record not found.")

        attendance.delete()
        logger.info(f"Attendance deleted: id={attendance_id}")


























