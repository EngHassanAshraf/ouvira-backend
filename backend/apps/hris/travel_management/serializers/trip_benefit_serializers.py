from rest_framework import serializers
from apps.hris.travel_management.models import BusinessTripBenefit


class BusinessTripBenefitSerializer(serializers.ModelSerializer):
    """
    Benefit ro'yxati uchun.
    List of benefits.
    """
    class Meta:
        model  = BusinessTripBenefit
        fields = ["id", "name", "code", "is_fixed"]


class BusinessTripBenefitCreateSerializer(serializers.ModelSerializer):
    """
    Yangi custom benefit qo'shish uchun (HR).
    Create a new custom benefit (HR only).
    """
    class Meta:
        model  = BusinessTripBenefit
        fields = ["id", "name", "code"]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Benefit name cannot be empty.")
        return value

