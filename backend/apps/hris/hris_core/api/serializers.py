from rest_framework import serializers
from django.utils.translation import gettext_lazy as _


from apps.hris.hris_core.models import Location
from apps.hris.hris_core.models.employee import Employee
from apps.hris.hris_core.models.organization import Department, JobTitle, Position
from apps.hris.hris_core.models.employment import Employment
from apps.hris.hris_core.models.attendance import AttendanceRecord


class LocationSerializers(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'city', 'country', 'is_active']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", 'name']



class JobTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobTitle
        fields = ["id", "title", "description"]



class EmployeeListSerializer(serializers.ModelSerializer):
    """
    UZB: Xodimlarni ro'yhattan o'tkazish faqat asosiy maydonlar
    ENG: for listing employee with basic information
    """
    full_name = serializers.SerializerMethodField
    department = DepartmentSerializer(read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    class Meta:
        model = Employee
        fields = [
            'id',
            'employee_id',
            'full_name',
            'first_name',
            'last_name',
            'department',
            'location_name',
            'national_id',
            'contact_number'
        ]



class EmployeeCreateSerializer(serializers.ModelSerializer):
    """
    UZB: Yangi xodim yaratish uchun barcha malumotlarni qabulqilish uchun
    ENG: for create a new employye with full data validate
    """

    class Meta:
        model = Employee
        fields = [
            'employee_id', 'first_name', 'last_name', 'national_id',
            'nationality', 'gender', 'marital_status', 'contact_number',
            'personal_email', 'location', 'department'
        ]
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



class EmploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employment
        fields = [
            "id",
            "employee",
            "hire_date",
            "status",
            "employment_type",
            "contract_start_date",
            "contract_end_date",
        ]


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = [
            "id",
            "job_title",
            "department",
            "location",
            "reports_to",
            "is_active"
        ]


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = [
            "id",
            "employee",
            "date",
            "check_in_time",
            "check_out_time",
            "status",
        ]