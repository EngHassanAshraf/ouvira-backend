from django.db.models import QuerySet
from apps.hris.hris_core.models.attendance import AttendanceRecord

class AttendanceSelector:
    @staticmethod
    def get_by_employee(employee_id: int)-> QuerySet:
        """
            Xodimlarning barcha yozuvlarini olish uchun
            To get all employee records
        """
        return AttendanceRecord.objects.filter(
            employee_id=employee_id, is_deleted=False
        ).order_by("-date")


    @staticmethod
    def get_by_date(employee_id:int, date)-> AttendanceRecord | None:
        """
        Xodimning muayyan kundagi davomat yozuvini olish
        Get an employee attendance record for a specific day
        """
        return AttendanceRecord.objects.filter(
            employee_id=employee_id, date=date, is_deleted=False
        ).first()

    @staticmethod
    def get_detail(attendance_id: int, employee_id: int)-> AttendanceRecord:
        """
        Bitta davomat yozuvini olish.
        """
        return AttendanceRecord.objects.get(
            id=attendance_id, employee_id=employee_id, is_deleted=False
        )