"""
Termination Request Serializers / Tugatish So'rovlari Serializerlari

Serializers for resignation and termination requests
Iste'fo va tugatish so'rovlari uchun serializerlar
"""

from rest_framework import serializers
from apps.hris.termination.models import TerminationRequest
from apps.hris.hris_core.models import Employee


class TerminationRequestListSerializer(serializers.ModelSerializer):
    """
    List serializer for termination requests
    Tugatish so'rovlari ro'yxati serializeri
    """
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_position = serializers.CharField(source='employee.position.name', read_only=True)
    termination_type_display = serializers.CharField(source='get_termination_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_until_final_working_day = serializers.IntegerField(read_only=True)
    can_be_withdrawn = serializers.BooleanField(read_only=True)

    class Meta:
        model = TerminationRequest
        fields = [
            'id',
            'employee',
            'employee_name',
            'employee_position',
            'termination_type',
            'termination_type_display',
            'status',
            'status_display',
            'is_voluntary',
            'submission_date',
            'final_working_day',
            'days_until_final_working_day',
            'can_be_withdrawn',
            'created_at',
            'updated_at'
        ]


class TerminationRequestDetailSerializer(serializers.ModelSerializer):
    """
    Detail serializer for termination requests
    Tugatish so'rovlari tafsilot serializeri
    """
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_position = serializers.CharField(source='employee.position.name', read_only=True)
    employee_department = serializers.CharField(source='employee.department.name', read_only=True)

    termination_type_display = serializers.CharField(source='get_termination_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    requested_by_name = serializers.CharField(source='requested_by.full_name', read_only=True)
    approved_by_manager_name = serializers.CharField(source='approved_by_manager.full_name', read_only=True)
    approved_by_gm_name = serializers.CharField(source='approved_by_gm.full_name', read_only=True)
    rejected_by_name = serializers.CharField(source='rejected_by.full_name', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.full_name', read_only=True)

    days_until_final_working_day = serializers.IntegerField(read_only=True)
    can_be_withdrawn = serializers.BooleanField(read_only=True)
    requires_exit_interview = serializers.BooleanField(read_only=True)

    # Related data
    has_settlement = serializers.SerializerMethodField()
    has_exit_interview = serializers.SerializerMethodField()
    warning_count = serializers.SerializerMethodField()

    class Meta:
        model = TerminationRequest
        fields = [
            'id',
            # Employee info
            'employee',
            'employee_name',
            'employee_email',
            'employee_position',
            'employee_department',
            # Termination info
            'termination_type',
            'termination_type_display',
            'status',
            'status_display',
            'reason',
            'is_voluntary',
            # Dates
            'submission_date',
            'final_working_day',
            'notice_period_days',
            'days_until_final_working_day',
            # Approvals
            'requested_by',
            'requested_by_name',
            'approved_by_manager',
            'approved_by_manager_name',
            'manager_approval_date',
            'approved_by_gm',
            'approved_by_gm_name',
            'gm_approval_date',
            # Rejection
            'rejected_by',
            'rejected_by_name',
            'rejection_date',
            'rejection_reason',
            # Withdrawal
            'withdrawal_request_date',
            'withdrawal_reason',
            'can_be_withdrawn',
            # Processing
            'processed_by',
            'processed_by_name',
            'processed_date',
            # Additional
            'notes',
            'attachment',
            'requires_exit_interview',
            # Related
            'has_settlement',
            'has_exit_interview',
            'warning_count',
            # Timestamps
            'created_at',
            'updated_at'
        ]

    def get_has_settlement(self, obj):
        return hasattr(obj, 'settlement')

    def get_has_exit_interview(self, obj):
        return hasattr(obj, 'exit_interview')

    def get_warning_count(self, obj):
        return obj.warnings.count() if hasattr(obj, 'warnings') else 0


class ResignationCreateSerializer(serializers.Serializer):
    """
    Serializer for submitting resignation
    Iste'fo yuborish serializeri
    """
    reason = serializers.CharField(required=True, max_length=5000)
    notice_period_days = serializers.IntegerField(default=30, min_value=0, max_value=90)
    attachment = serializers.FileField(required=False, allow_null=True)

    def validate_reason(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Reason must be at least 10 characters long"
            )
        return value


class ResignationWithdrawSerializer(serializers.Serializer):
    """
    Serializer for withdrawing resignation
    Iste'foni qaytarib olish serializeri
    """
    withdrawal_reason = serializers.CharField(required=True, max_length=1000)

    def validate_withdrawal_reason(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Withdrawal reason must be at least 10 characters long"
            )
        return value


class TerminationApprovalSerializer(serializers.Serializer):
    """
    Serializer for approving termination/resignation
    Tugatish/iste'foni tasdiqlash serializeri
    """
    notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class TerminationRejectionSerializer(serializers.Serializer):
    """
    Serializer for rejecting termination/resignation
    Tugatish/iste'foni rad etish serializeri
    """
    rejection_reason = serializers.CharField(required=True, max_length=2000)

    def validate_rejection_reason(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Rejection reason must be at least 10 characters long"
            )
        return value


class BehavioralTerminationCreateSerializer(serializers.Serializer):
    """
    Serializer for initiating behavioral termination
    Xulq-atvor tugatishini boshlash serializeri
    """
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(is_deleted=False)
    )
    violation_description = serializers.CharField(required=True, max_length=5000)
    is_gross_violation = serializers.BooleanField(default=False)
    attachment = serializers.FileField(required=False, allow_null=True)

    def validate_violation_description(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Violation description must be at least 20 characters long"
            )
        return value


class PerformanceTerminationCreateSerializer(serializers.Serializer):
    """
    Serializer for initiating performance termination
    Ish faoliyati tugatishini boshlash serializeri
    """
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(is_deleted=False)
    )
    performance_issues = serializers.CharField(required=True, max_length=5000)
    evaluation_scores = serializers.ListField(
        child=serializers.DecimalField(max_digits=5, decimal_places=2),
        required=False,
        allow_null=True
    )
    attachment = serializers.FileField(required=False, allow_null=True)


class ProbationTerminationCreateSerializer(serializers.Serializer):
    """
    Serializer for initiating probation termination
    Sinov muddati tugatishini boshlash serializeri
    """
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(is_deleted=False)
    )
    probation_reason = serializers.CharField(required=True, max_length=5000)
    attachment = serializers.FileField(required=False, allow_null=True)


class MedicalTerminationCreateSerializer(serializers.Serializer):
    """
    Serializer for initiating medical termination
    Tibbiy tugatishni boshlash serializeri
    """
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(is_deleted=False)
    )
    medical_condition = serializers.CharField(required=True, max_length=5000)
    is_reassignment_possible = serializers.BooleanField(required=True)
    medical_reports = serializers.FileField(required=False, allow_null=True)


class LayoffCreateSerializer(serializers.Serializer):
    """
    Serializer for initiating layoff
    Qisqartirishni boshlash serializeri
    """
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(is_deleted=False)
    )
    layoff_reason = serializers.CharField(required=True, max_length=5000)
    department_restructuring = serializers.BooleanField(default=False)
    economic_downturn = serializers.BooleanField(default=False)
    attachment = serializers.FileField(required=False, allow_null=True)


class DeceasedEmployeeSerializer(serializers.Serializer):
    """
    Serializer for processing deceased employee
    Vafot etgan xodimni qayta ishlash serializeri
    """
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(is_deleted=False)
    )
    date_of_death = serializers.DateField(required=True)
    next_of_kin_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    next_of_kin_relationship = serializers.CharField(required=False, allow_blank=True, max_length=50)
    next_of_kin_contact = serializers.CharField(required=False, allow_blank=True, max_length=200)
    death_certificate = serializers.FileField(required=False, allow_null=True)