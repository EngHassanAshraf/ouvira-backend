from rest_framework import serializers
from apps.hris.travel_management.models import TravelRequest


class TravelRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    def get_employee_name(self, obj):
        return obj.employee.full_name if obj.employee else None

    class Meta:
        model = TravelRequest
        fields = [
            "id",
            "employee",
            "employee_name",
            "destination",
            "start_date",
            "end_date",
            "purpose",
            "estimated_cost",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class TravelRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelRequest
        fields = ["destination", "start_date", "end_date", "purpose", "estimated_cost"]

    def validate(self, attrs):
        if attrs.get("start_date") and attrs.get("end_date"):
            if attrs["start_date"] > attrs["end_date"]:
                raise serializers.ValidationError(
                    {"end_date": "end_date must be on or after start_date."}
                )
        return attrs
