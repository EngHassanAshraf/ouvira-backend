from rest_framework import serializers
from apps.hris.leave_management.models import (
    LeaveType, LeaveRequest, LeaveBalance,
    LeaveBalanceAdjustment, LeaveActivityLog
)


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ["id", "name", "code", "days_per_year", "is_active"]


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    def validate_attachment(self, value):
        if value is None:
            return value
        max_size = 5 * 1024 * 1024 # 5 mb bytesda
        if value.size > max_size:
            raise serializers.ValidationError("Fail size exceeds the 5mb limit")

        #file turi PDF , LPG, PNG, DOCX
        allowed_types = [
           "application/pdf",
            "image/jpeg",
            "image/png",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]
        if value.content_type  not in allowed_types:
            raise serializers.ValidationError(
                "Unsupported file type. Alowed types: PDF JPG PNG DOCX"
            )
        
        return value



    class Meta:
        model = LeaveRequest
        fields = [
            "id", "leave_type", "start_date",
            "end_date", "details", "attachment",
        ]


class LeaveRequestListSerializer(serializers.ModelSerializer):
    """Ro'yxat uchun — qisqa ma'lumot"""
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)
    employee_name = serializers.SerializerMethodField()

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"

    class Meta:
        model = LeaveRequest
        fields = [
            "id", "leave_type", "leave_type_name",
            "employee_name", "start_date", "end_date",
            "duration", "status", "created_at",
        ]


class LeaveRequestDetailSerializer(serializers.ModelSerializer):
    """Detail uchun — to'liq ma'lumot"""
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)
    employee_name = serializers.SerializerMethodField()
    manager_approved_by_name = serializers.SerializerMethodField()
    hr_approved_by_name = serializers.SerializerMethodField()
    declined_by_name = serializers.SerializerMethodField()

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"

    def get_manager_approved_by_name(self, obj):
        if obj.manager_approved_by:
            return f"{obj.manager_approved_by.first_name} {obj.manager_approved_by.last_name}"
        return None

    def get_hr_approved_by_name(self, obj):
        if obj.hr_approved_by:
            return f"{obj.hr_approved_by.first_name} {obj.hr_approved_by.last_name}"
        return None

    def get_declined_by_name(self, obj):
        if obj.declined_by:
            return f"{obj.declined_by.first_name} {obj.declined_by.last_name}"
        return None

    class Meta:
        model = LeaveRequest
        fields = [
            "id", "leave_type", "leave_type_name",
            "employee_name", "start_date", "end_date",
            "duration", "details", "attachment", "status",
            "created_by_id", "manager_approved_by_name", "manager_approved_at",
            "hr_approved_by_name", "hr_approved_at",
            "declined_by_name", "declined_at", "decline_reason",
            "interruption_date", "interrupted_at",
            "created_at", "updated_at",
        ]


class DeclineSerializer(serializers.Serializer):
    """Rad etish uchun — reason majburiy"""
    reason = serializers.CharField(min_length=1)


class InterruptSerializer(serializers.Serializer):
    """Interruption uchun"""
    interruption_date = serializers.DateField()


class BulkActionSerializer(serializers.Serializer):
    """Bulk approve/decline uchun"""
    leave_request_ids = serializers.ListField(
        child=serializers.IntegerField()
    )
    reason = serializers.CharField(required=False, allow_blank=True)


class LeaveBalanceSerializer(serializers.ModelSerializer):
    """Balans ko'rish uchun"""
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)
    remaining_days = serializers.DecimalField(
        max_digits=5, decimal_places=1, read_only=True
    )

    class Meta:
        model = LeaveBalance
        fields = [
            "id", "leave_type", "leave_type_name",
            "year", "total_days", "used_days",
            "adjusted_days", "remaining_days",
        ]


class LeaveBalanceAdjustSerializer(serializers.Serializer):
    """Menejer qo'lda balans o'zgartirish uchun"""
    leave_type_id = serializers.IntegerField()
    year = serializers.IntegerField()
    days = serializers.DecimalField(max_digits=5, decimal_places=1)
    justification = serializers.CharField(min_length=1)


class LeaveActivityLogSerializer(serializers.ModelSerializer):
    """Activity log uchun"""
    performed_by_name = serializers.SerializerMethodField()
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return f"{obj.performed_by.first_name} {obj.performed_by.last_name}"
        return None

    class Meta:
        model = LeaveActivityLog
        fields = [
            "id",
            "leave_request",
            "action",
            'action_display',
            "performed_by_name",
            "note",
            "created_at",
        ]

