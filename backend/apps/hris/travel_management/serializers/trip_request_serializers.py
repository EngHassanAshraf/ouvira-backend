from rest_framework import serializers
from apps.hris.travel_management.models import (
    BusinessTripRequest,
    BusinessTripActivityLog,
)
from apps.hris.travel_management.serializers.trip_benefit_serializers import (
    BusinessTripBenefitSerializer,
)


class BusinessTripRequestCreateSerializer(serializers.Serializer):
    """
    Yangi so'rov yaratish uchun.
    Create a new business trip request.
    """
    employee_id  = serializers.IntegerField(required=False)  # on_behalf_of uchun
    destination  = serializers.CharField(max_length=255)
    start_date   = serializers.DateField()
    end_date     = serializers.DateField()
    details      = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    benefit_ids  = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=True
    )
    attachments  = serializers.ListField(
        child=serializers.URLField(), required=False, allow_empty=True
    )

    def validate(self, data):
        if data["end_date"] < data["start_date"]:
            raise serializers.ValidationError(
                "End date must be the same as or later than the start date."
            )
        return data


class BusinessTripRequestUpdateSerializer(serializers.Serializer):
    """
    So'rovni tahrirlash uchun (faqat PENDING da).
    Update a request (only when PENDING).
    """
    destination = serializers.CharField(max_length=255, required=False)
    start_date  = serializers.DateField(required=False)
    end_date    = serializers.DateField(required=False)
    details     = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    benefit_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )
    attachments = serializers.ListField(
        child=serializers.URLField(), required=False
    )

    def validate(self, data):
        start_date = data.get("start_date")
        end_date   = data.get("end_date")
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                "End date must be the same as or later than the start date."
            )
        return data


class BusinessTripActivityLogSerializer(serializers.ModelSerializer):
    """
    Activity log uchun.
    Activity log serializer.
    """
    performed_by_name = serializers.SerializerMethodField()
    action_display    = serializers.CharField(source="get_action_display", read_only=True)

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return f"{obj.performed_by.first_name} {obj.performed_by.last_name}"
        return None

    class Meta:
        model  = BusinessTripActivityLog
        fields = [
            "id", "action", "action_display",
            "performed_by_name", "note", "created_at",
        ]


class BusinessTripRequestListSerializer(serializers.ModelSerializer):
    """
    Ro'yxat uchun — qisqa ma'lumot.
    List view — short info.
    """
    employee_name = serializers.SerializerMethodField()
    benefits      = BusinessTripBenefitSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"

    class Meta:
        model  = BusinessTripRequest
        fields = [
            "id", "employee_name", "destination",
            "start_date", "end_date", "duration",
            "benefits", "status", "status_display", "created_at",
        ]


class BusinessTripRequestDetailSerializer(serializers.ModelSerializer):
    """
    Detail uchun — to'liq ma'lumot + activity log.
    Detail view — full info + activity log.
    """
    employee_name           = serializers.SerializerMethodField()
    created_by_name         = serializers.SerializerMethodField()
    manager_approved_by_name = serializers.SerializerMethodField()
    hr_approved_by_name     = serializers.SerializerMethodField()
    declined_by_name        = serializers.SerializerMethodField()
    interrupted_by_name     = serializers.SerializerMethodField()
    benefits                = BusinessTripBenefitSerializer(many=True, read_only=True)
    activity_logs           = BusinessTripActivityLogSerializer(many=True, read_only=True)
    status_display          = serializers.CharField(source="get_status_display", read_only=True)

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return None

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

    def get_interrupted_by_name(self, obj):
        if obj.interrupted_by:
            return f"{obj.interrupted_by.first_name} {obj.interrupted_by.last_name}"
        return None

    class Meta:
        model  = BusinessTripRequest
        fields = [
            "id", "employee_name", "created_by_name",
            "destination", "start_date", "end_date", "duration",
            "details", "benefits", "attachments",
            "status", "status_display",
            "manager_approved_by_name", "manager_approved_at",
            "hr_approved_by_name", "hr_approved_at",
            "declined_by_name", "declined_at", "decline_reason",
            "interrupted_by_name", "interruption_date", "interrupted_at",
            "created_at", "updated_at",
            "activity_logs",
        ]


class DeclineSerializer(serializers.Serializer):
    """Rad etish uchun — reason majburiy."""
    reason = serializers.CharField(min_length=1)


class InterruptSerializer(serializers.Serializer):
    """Safarni to'xtatish uchun."""
    interruption_date = serializers.DateField()


class BulkActionSerializer(serializers.Serializer):
    """Bulk approve/decline uchun."""
    trip_request_ids = serializers.ListField(
        child=serializers.IntegerField()
    )
    reason = serializers.CharField(required=False, allow_blank=True)
