from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.hris.hris_core.models import Location
from apps.hris.hris_core.models.employee import Employee
from apps.hris.hris_core.models.organization import Department, JobTitle, Position
from apps.hris.hris_core.models.employment import Employment
from apps.hris.hris_core.models.attendance import AttendanceRecord
from apps.hris.hris_core.models.employee_extensions import (
    EmployeeLeaveBalance,
    EmployeeAllowance,
    EmployeeBankDetail,
    EmployeeCost,
    EmployeeDocument,
    EmployeeBusinessTripBalance,
)


# ── Shared / Nested ────────────────────────────────────────────────────────────

class LocationSerializers(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name", "address", "city", "country", "is_active"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name"]


class JobTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobTitle
        fields = ["id", "title", "description"]


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ["id", "job_title", "department", "location", "reports_to", "is_active"]


# ── Employment ─────────────────────────────────────────────────────────────────

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


class EmploymentNestedSerializer(serializers.ModelSerializer):
    """Lightweight employment info embedded in employee responses."""

    # Maps DB status values → Figma badge display labels
    STATUS_BADGE_MAP = {
        "active":        "active",
        "probation":     "probation",
        "on_leave":      "time-off",
        "business_trip": "business trip",
        "terminated":    "fired",
    }

    status_badge = serializers.SerializerMethodField()

    def get_status_badge(self, obj):
        return self.STATUS_BADGE_MAP.get(obj.status, obj.status)

    class Meta:
        model = Employment
        fields = ["id", "hire_date", "status", "status_badge", "employment_type"]


# ── Extension serializers ──────────────────────────────────────────────────────

class EmployeeLeaveBalanceSerializer(serializers.ModelSerializer):
    remaining_days = serializers.ReadOnlyField()
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)

    class Meta:
        model = EmployeeLeaveBalance
        fields = [
            "id",
            "leave_type",
            "leave_type_name",
            "total_days",
            "used_days",
            "remaining_days",
            "reset_date",
        ]


class EmployeeAllowanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAllowance
        fields = ["id", "name", "value"]


class EmployeeBankDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeBankDetail
        fields = ["id", "bank_iban", "bank_name"]


class EmployeeCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeCost
        fields = ["id", "cost_type", "value", "cost_date"]


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = ["id", "document_type", "file", "file_name", "created_at"]
        read_only_fields = ["file_name", "created_at"]


class EmployeeBusinessTripBalanceSerializer(serializers.ModelSerializer):
    remaining_balance = serializers.ReadOnlyField()

    class Meta:
        model = EmployeeBusinessTripBalance
        fields = ["id", "total_balance", "used_balance", "remaining_balance", "reset_date"]


# ── Employee List (table view) ─────────────────────────────────────────────────

class ReportingManagerSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Employee
        fields = ["id", "employee_id", "full_name"]


class EmployeeListSerializer(serializers.ModelSerializer):
    """
    Columns required by the Figma employee list table.
    """
    # Status badge display map — aligns DB values to Figma badge labels
    _STATUS_BADGE_MAP = {
        "active":        "active",
        "probation":     "probation",
        "on_leave":      "time-off",
        "business_trip": "business trip",
        "terminated":    "fired",
    }

    full_name = serializers.ReadOnlyField()
    department = DepartmentSerializer(read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    reporting_manager = ReportingManagerSerializer(read_only=True)
    employee_status = serializers.ReadOnlyField()
    employee_status_badge = serializers.SerializerMethodField()
    # Flatten the latest employment fields for the table
    hire_date = serializers.SerializerMethodField()
    employment_type = serializers.SerializerMethodField()
    employment_type_display = serializers.SerializerMethodField()

    def _latest_employment(self, obj):
        employments = getattr(obj, "active_employments", None)
        if employments:
            return employments[0]
        return None

    def get_employee_status_badge(self, obj):
        return self._STATUS_BADGE_MAP.get(obj.employee_status, obj.employee_status)

    def get_hire_date(self, obj):
        emp = self._latest_employment(obj)
        return emp.hire_date if emp else None

    def get_employment_type(self, obj):
        emp = self._latest_employment(obj)
        return emp.employment_type if emp else None

    def get_employment_type_display(self, obj):
        emp = self._latest_employment(obj)
        if emp:
            return emp.get_employment_type_display()
        return None

    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_id",
            "full_name",
            "first_name",
            "last_name",
            "personal_email",
            "contact_number",
            "nationality",
            "department",
            "location_name",
            "national_id",
            "reporting_manager",
            "employee_status",
            "employee_status_badge",
            "employment_type",
            "employment_type_display",
            "hire_date",
            "updated_at",
        ]


# ── Employee Create ────────────────────────────────────────────────────────────

class EmployeeCreateSerializer(serializers.ModelSerializer):
    """Accepts all fields from the New Employee form (personal + job + account tabs)."""

    class Meta:
        model = Employee
        fields = [
            # Core
            "employee_id",
            "first_name",
            "last_name",
            # Photo
            "photo",
            # Identity
            "national_id",
            "national_id_job_title",
            "national_id_status",
            "passport_number",
            "visa_number",
            "iqama_status",
            "fingerprint_id",
            "nationality",
            # Personal
            "date_of_birth",
            "gender",
            "marital_status",
            "contact_number",
            "secondary_phone",
            "personal_email",
            "work_email",
            "address",
            # Job
            "job_title",
            # Relations
            "location",
            "department",
            "reporting_manager",
            # System
            "is_system_user",
        ]
        extra_kwargs = {
            "employee_id":   {"required": True},
            "date_of_birth": {"required": True},
            "gender":        {"required": True},
            "company":       {"required": False},
        }

    def validate_national_id(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                _("National ID must contain only digits.")
            )
        if len(value) != 10:
            raise serializers.ValidationError(
                _("National ID must be exactly 10 digits.")
            )
        return value

    def validate_employee_id(self, value):
        from django.conf import settings
        prefix = getattr(settings, "EMPLOYEE_ID_PREFIX", "s")
        if not value.startswith(prefix):
            raise serializers.ValidationError(
                _(f"Employee ID must start with '{prefix}' followed by a number (e.g. {prefix}1001).")
            )
        suffix = value[len(prefix):]
        if not suffix.isdigit():
            raise serializers.ValidationError(
                _(f"Employee ID must be '{prefix}' followed by digits only (e.g. {prefix}1001).")
            )
        return value


# ── Employee Update ────────────────────────────────────────────────────────────

class EmployeeUpdateSerializer(EmployeeCreateSerializer):
    """Same fields as create but all optional for PATCH."""

    class Meta(EmployeeCreateSerializer.Meta):
        extra_kwargs = {
            field: {"required": False}
            for field in EmployeeCreateSerializer.Meta.fields
        }


# ── Employee Detail (profile view) ────────────────────────────────────────────

class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Full read-only profile — all tabs."""

    _STATUS_BADGE_MAP = {
        "active":        "active",
        "probation":     "probation",
        "on_leave":      "time-off",
        "business_trip": "business trip",
        "terminated":    "fired",
    }

    full_name = serializers.ReadOnlyField()
    department = DepartmentSerializer(read_only=True)
    location = LocationSerializers(read_only=True)
    reporting_manager = ReportingManagerSerializer(read_only=True)
    job_title = JobTitleSerializer(read_only=True)
    employee_status = serializers.ReadOnlyField()
    employee_status_badge = serializers.SerializerMethodField()
    employments = EmploymentNestedSerializer(many=True, read_only=True)
    leave_balances = EmployeeLeaveBalanceSerializer(many=True, read_only=True)
    allowances = EmployeeAllowanceSerializer(many=True, read_only=True)
    bank_detail = EmployeeBankDetailSerializer(read_only=True)
    costs = EmployeeCostSerializer(many=True, read_only=True)
    documents = EmployeeDocumentSerializer(many=True, read_only=True)
    business_trip_balance = EmployeeBusinessTripBalanceSerializer(read_only=True)

    def get_employee_status_badge(self, obj):
        return self._STATUS_BADGE_MAP.get(obj.employee_status, obj.employee_status)

    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_id",
            "full_name",
            "first_name",
            "last_name",
            "photo",
            # Identity
            "national_id",
            "national_id_job_title",
            "national_id_status",
            "passport_number",
            "visa_number",
            "iqama_status",
            "fingerprint_id",
            "nationality",
            # Personal
            "date_of_birth",
            "gender",
            "marital_status",
            "contact_number",
            "secondary_phone",
            "personal_email",
            "work_email",
            "address",
            # Job
            "job_title",
            # Relations
            "department",
            "location",
            "reporting_manager",
            # System
            "is_system_user",
            "employee_status",
            "employee_status_badge",
            # Timestamps
            "created_at",
            "updated_at",
            "deleted_at",
            # Nested
            "employments",
            "leave_balances",
            "allowances",
            "bank_detail",
            "costs",
            "documents",
            "business_trip_balance",
        ]


# ── Attendance ─────────────────────────────────────────────────────────────────

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


# ── Full Employee Create (multi-tab single payload) ────────────────────────────

class EmploymentCreateInlineSerializer(serializers.Serializer):
    """Employment tab — inline within the full employee create payload."""
    hire_date = serializers.DateField()
    status = serializers.ChoiceField(
        choices=Employment.StatusChoice.choices,
        default=Employment.StatusChoice.PROBATION,
    )
    employment_type = serializers.ChoiceField(
        choices=Employment.TypeChoice.choices,
        default=Employment.TypeChoice.FULL_TIME,
    )
    contract_start_date = serializers.DateField(required=False, allow_null=True)
    contract_end_date = serializers.DateField(required=False, allow_null=True)


class AllowanceInlineSerializer(serializers.Serializer):
    """Single allowance entry within the full create payload."""
    name = serializers.CharField(max_length=255)
    value = serializers.DecimalField(max_digits=12, decimal_places=2)


class BankDetailInlineSerializer(serializers.Serializer):
    """Bank details tab — inline within the full employee create payload."""
    bank_iban = serializers.CharField(max_length=34)
    bank_name = serializers.CharField(max_length=255, required=False, allow_blank=True)


class BusinessTripBalanceInlineSerializer(serializers.Serializer):
    """Business trip allowances tab — inline within the full employee create payload."""
    total_balance = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    reset_date = serializers.DateField(required=False, allow_null=True)


class EmployeeFullCreateSerializer(serializers.Serializer):
    """
    Single-payload serializer for POST /employees/full/
    Accepts all form tabs at once.
    """
    # ── Personal Information tab ───────────────────────────────────
    employee_id = serializers.CharField(max_length=50)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    photo = serializers.ImageField(required=False, allow_null=True)
    national_id = serializers.CharField(max_length=20)
    national_id_job_title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    national_id_status = serializers.ChoiceField(
        choices=Employee.NationalIDStatusChoice.choices, required=False, allow_null=True
    )
    passport_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    visa_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    iqama_status = serializers.ChoiceField(
        choices=Employee.IqamaStatusChoice.choices, required=False, allow_null=True
    )
    fingerprint_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    nationality = serializers.CharField(max_length=100, default="Saudi Arabian")
    date_of_birth = serializers.DateField()
    gender = serializers.ChoiceField(choices=Employee.GenderChoice.choices)
    marital_status = serializers.ChoiceField(
        choices=Employee.MaritalStatusChoice.choices, required=False, allow_null=True
    )
    contact_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    secondary_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    personal_email = serializers.EmailField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True)

    # ── Job Details tab ────────────────────────────────────────────
    job_title = serializers.PrimaryKeyRelatedField(
        queryset=JobTitle.objects.all(), required=False, allow_null=True
    )
    location = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.hris.hris_core.models', fromlist=['Location']).Location.objects.all(),
        required=False, allow_null=True,
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.hris.hris_core.models', fromlist=['Department']).Department.objects.all(),
        required=False, allow_null=True,
    )
    reporting_manager = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), required=False, allow_null=True
    )

    # ── Account Information tab ────────────────────────────────────
    # work_email is the system/login email stored on Employee
    work_email = serializers.EmailField(required=False, allow_null=True)
    is_system_user = serializers.BooleanField(default=False)
    # password fields — only used when is_system_user=True
    password = serializers.CharField(
        max_length=128, required=False, allow_blank=True, write_only=True,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        max_length=128, required=False, allow_blank=True, write_only=True,
        style={"input_type": "password"},
    )

    # ── Employment tab (optional) ──────────────────────────────────
    employment = EmploymentCreateInlineSerializer(required=False)

    # ── Allowances tab (optional list) ────────────────────────────
    allowances = AllowanceInlineSerializer(many=True, required=False)

    # ── Bank Details tab (optional) ───────────────────────────────
    bank_detail = BankDetailInlineSerializer(required=False)

    # ── Business Trip Allowances tab (optional) ───────────────────
    business_trip_balance = BusinessTripBalanceInlineSerializer(required=False)

    def validate_national_id(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                _("National ID must be exactly 10 digits.")
            )
        return value

    def validate_employee_id(self, value):
        from django.conf import settings
        prefix = getattr(settings, "EMPLOYEE_ID_PREFIX", "s")
        if not value.startswith(prefix) or not value[len(prefix):].isdigit():
            raise serializers.ValidationError(
                _(f"Employee ID must be '{prefix}' followed by digits (e.g. {prefix}1001).")
            )
        return value

    def validate(self, attrs):
        is_system_user = attrs.get("is_system_user", False)
        password = attrs.get("password", "")
        password_confirm = attrs.get("password_confirm", "")

        if is_system_user:
            if not password:
                raise serializers.ValidationError(
                    {"password": _("Password is required when creating a system user.")}
                )
            if password != password_confirm:
                raise serializers.ValidationError(
                    {"password_confirm": _("Passwords do not match.")}
                )
            # Basic strength check
            if len(password) < 8:
                raise serializers.ValidationError(
                    {"password": _("Password must be at least 8 characters.")}
                )

        return attrs
