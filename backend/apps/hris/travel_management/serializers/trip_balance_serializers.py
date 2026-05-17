from rest_framework import serializers
from apps.hris.travel_management.models import (
    BusinessTripBalance,
    BusinessTripBalanceAdjustment,
)


class BusinessTripBalanceAdjustmentSerializer(serializers.ModelSerializer):
    """
    Adjustment tarixi uchun — delta display (+3 / -2).
    Adjustment history — with delta display.
    """
    performed_by_name  = serializers.SerializerMethodField()
    adjustment_display = serializers.SerializerMethodField()

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return f"{obj.performed_by.first_name} {obj.performed_by.last_name}"
        return None

    def get_adjustment_display(self, obj):
        sign = "+" if obj.adjustment_type == "add" else "-"
        return f"{sign}{obj.days}"

    class Meta:
        model  = BusinessTripBalanceAdjustment
        fields = [
            "id", "adjustment_type", "adjustment_display",
            "days", "reason", "performed_by_name", "created_at",
        ]


class BusinessTripBalanceSerializer(serializers.ModelSerializer):
    """
    Balans ko'rish uchun — remaining_days bilan.
    Balance view — with remaining_days.
    """
    employee_name  = serializers.SerializerMethodField()
    remaining_days = serializers.DecimalField(
        max_digits=5, decimal_places=1, read_only=True
    )

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"

    class Meta:
        model  = BusinessTripBalance
        fields = [
            "id", "employee_name", "year",
            "total_days", "used_days", "remaining_days",
        ]


class BusinessTripBalanceDetailSerializer(serializers.ModelSerializer):
    """
    Balans detail — adjustment tarixi bilan.
    Balance detail — with adjustment history.
    """
    employee_name  = serializers.SerializerMethodField()
    remaining_days = serializers.DecimalField(
        max_digits=5, decimal_places=1, read_only=True
    )
    adjustments    = BusinessTripBalanceAdjustmentSerializer(many=True, read_only=True)

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"

    class Meta:
        model  = BusinessTripBalance
        fields = [
            "id", "employee_name", "year",
            "total_days", "used_days", "remaining_days",
            "adjustments",
        ]


class BusinessTripBalanceAdjustSerializer(serializers.Serializer):
    """
    HR tomonidan balans o'zgartirish uchun.
    Balance adjustment by HR.
    """
    adjustment_type = serializers.ChoiceField(choices=["add", "deduct"])
    days            = serializers.DecimalField(max_digits=5, decimal_places=1, min_value=0.1)
    reason          = serializers.CharField(required=False, allow_blank=True)


class BusinessTripBulkAdjustSerializer(serializers.Serializer):
    """
    Bir vaqtda ko'p xodim balansini o'zgartirish.
    Bulk balance adjustment for multiple employees.
    """
    employee_ids    = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=True
    )
    adjustment_type = serializers.ChoiceField(choices=["add", "deduct"])
    days            = serializers.DecimalField(max_digits=5, decimal_places=1, min_value=0.1)
    reason          = serializers.CharField(required=False, allow_blank=True)


class BusinessTripCSVImportSerializer(serializers.Serializer):
    """
    CSV fayldan balanslarni import qilish.
    Import balances from CSV file.
    """
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.endswith(".csv"):
            raise serializers.ValidationError(
                "Only CSV files are allowed."
            )
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError(
                "File size exceeds 5MB limit."
            )
        return value


class BusinessTripBalanceAdjustmentLogSerializer(serializers.ModelSerializer):
    """
    Active Log uchun — barcha adjustmentlar tarixi.
    For Active Log — full adjustment history.
    """
    employee_name    = serializers.SerializerMethodField()
    performed_by_name = serializers.SerializerMethodField()
    adjustment_display = serializers.SerializerMethodField()
    year             = serializers.IntegerField(source="balance.year", read_only=True)

    def get_employee_name(self, obj):
        emp = obj.balance.employee
        return f"{emp.first_name} {emp.last_name}"

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return f"{obj.performed_by.first_name} {obj.performed_by.last_name}"
        return None

    def get_adjustment_display(self, obj):
        sign = "+" if obj.adjustment_type == "add" else "-"
        return f"{sign}{obj.days}"

    class Meta:
        model  = BusinessTripBalanceAdjustment
        fields = [
            "id", "employee_name", "year",
            "adjustment_type", "adjustment_display",
            "days", "reason", "performed_by_name", "created_at",
        ]
