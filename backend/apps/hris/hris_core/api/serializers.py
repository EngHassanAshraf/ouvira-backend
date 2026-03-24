from rest_framework import serializers
from apps.hris.hris_core.models import Location
from apps.hris.hris_core.models.employee import Employee
from django.utils.translation import gettext_lazy as _

class LocationSerializers(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'city', 'country', 'is_active']


class EmployeeListSerializer(serializers.ModelSerializer):
    """
    UZB: Xodimlarni ro'yhattan o'tkazish faqat asosiy maydonlar
    ENG: for listing employee with basic information
    """

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'full_name', 'first_name', 'last_name',
            'location_name', 'national_id', 'contact_number'
        ]

        def get_full_name(self, obj):
            return f"{obj.first_name} {obj.last_name}"

class EmployeeCreateSerializer(serializers.ModelSerializer):
    """
    UZB: Yangi xodim yaratish uchun barcha malumotlarni qabulqilish uchun
    ENG: for create a new employye with full data validate
    """

    class Meta:
        model = Employee
        fields = '__all__'
        extra_kwargs ={
            'company': {'required': False},
            'employee_id': {'required': True}
        }

    def validate_national_id(self, value):
        """
        KSR requirement: National ID / IQMA must be exactly 10digit.
        """
        if not value.isdigit():
            raise serializers.ValidationError(_("National ID must contain only digits."))
        if len(value) != 10:
            raise serializers.ValidationError(_("National ID must be exactly 10 digits."))
        return value

    def validate_employee_id(self, value):
        """
        Employee ID takrorlanmasligini tekshirish (agar kerak bo'lsa)
        Check for duplicate Employee IDs (if necessary).
        """
        # Joriy kompaniya ichida tekshirish View darajasida qilinadi,
        # lekin bu yerda umumiy formatni tekshirish mumkin.
        return value