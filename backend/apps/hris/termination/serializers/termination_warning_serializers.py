"""
Termination Warning Serializers / Ogohlantirish Serializerlari

Serializers for absence and performance warnings
Davomat va ish faoliyati ogohlantirishlari uchun serializerlar
"""

from rest_framework import serializers
from apps.hris.termination.models import TerminationWarning
from apps.hris.hris_core.models import Employee


class TerminationWarningListSerializer(serializers.ModelSerializer):
    """
    List serializer for warnings
    Ogohlantirishlar ro'yxati serializeri
    """
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    warning_type_display = serializers.CharField(source='get_warning_type_display', read_only=True)
    warning_level_display = serializers.CharField(source='get_warning_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    issued_by_name = serializers.CharField(source='issued_by.full_name', read_only=True)
    is_final_warning = serializers.BooleanField(read_only=True)
    can_escalate_to_termination = serializers.BooleanField(read_only=True)

    class Meta:
        model = TerminationWarning
        fields = [
            'id',
            'employee',
            'employee_name',
            'warning_type',
            'warning_type_display',
            'warning_level',
            'warning_level_display',
            'status',
            'status_display',
            'issue_date',
            'absence_days_count',
            'evaluation_score',
            'issued_by',
            'issued_by_name',
            'is_final_warning',
            'can_escalate_to_termination',
            'created_at'
        ]


class TerminationWarningDetailSerializer(serializers.ModelSerializer):
    """
    Detail serializer for warnings
    Ogohlantirishlar tafsilot serializeri
    """
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_position = serializers.CharField(source='employee.position.name', read_only=True)
    employee_department = serializers.CharField(source='employee.department.name', read_only=True)

    warning_type_display = serializers.CharField(source='get_warning_type_display', read_only=True)
    warning_level_display = serializers.CharField(source='get_warning_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    issued_by_name = serializers.CharField(source='issued_by.full_name', read_only=True)

    is_final_warning = serializers.BooleanField(read_only=True)
    can_escalate_to_termination = serializers.BooleanField(read_only=True)

    escalated_to_termination_id = serializers.IntegerField(
        source='escalated_to_termination.id',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = TerminationWarning
        fields = [
            'id',
            # Employee info
            'employee',
            'employee_name',
            'employee_email',
            'employee_position',
            'employee_department',
            # Warning info
            'warning_type',
            'warning_type_display',
            'warning_level',
            'warning_level_display',
            'status',
            'status_display',
            'reason',
            'issue_date',
            # Absence details
            'absence_start_date',
            'absence_days_count',
            # Performance details
            'evaluation_score',
            'evaluation_period',
            # Delivery
            'sent_via_registered_mail',
            'registered_mail_tracking',
            'form_s6_attached',
            # Acknowledgment
            'acknowledged_date',
            'employee_response',
            # Issued by
            'issued_by',
            'issued_by_name',
            # Resolution
            'resolved_date',
            'resolution_notes',
            # Escalation
            'escalated_to_termination',
            'escalated_to_termination_id',
            'escalation_date',
            # Properties
            'is_final_warning',
            'can_escalate_to_termination',
            # Attachments
            'attachment',
            # Timestamps
            'created_at',
            'updated_at'
        ]


class AbsenceWarningCreateSerializer(serializers.Serializer):
    """
    Serializer for issuing absence warning
    Davomat ogohlantirishini berish serializeri
    """
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(is_deleted=False)
    )
    warning_type = serializers.ChoiceField(
        choices=[
            ('absence_egyptian', 'Absence Warning (Egyptian Law)'),
            ('absence_saudi', 'Absence Warning (Saudi Law)')
        ]
    )
    absence_start_date = serializers.DateField(required=True)
    absence_days_count = serializers.IntegerField(required=True, min_value=5, max_value=100)
    reason = serializers.CharField(required=True, max_length=5000)
    sent_via_registered_mail = serializers.BooleanField(default=False)
    registered_mail_tracking = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100
    )
    form_s6_attached = serializers.BooleanField(default=False)
    attachment = serializers.FileField(required=False, allow_null=True)

    def validate_absence_days_count(self, value):
        if value < 5:
            raise serializers.ValidationError(
                "Absence warning requires at least 5 days of absence"
            )
        return value

    def validate(self, data):
        # Saudi 2nd warning requires registered mail
        if (data.get('warning_type') == 'absence_saudi' and
                data.get('absence_days_count', 0) >= 10 and
                not data.get('sent_via_registered_mail')):
            raise serializers.ValidationError({
                'sent_via_registered_mail':
                    'Saudi Law requires 2nd warning (10+ days) via registered mail'
            })

        return data


class PerformanceWarningCreateSerializer(serializers.Serializer):
    """
    Serializer for issuing performance warning
    Ish faoliyati ogohlantirishini berish serializeri
    """
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(is_deleted=False)
    )
    evaluation_score = serializers.DecimalField(
        required=True,
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100
    )
    evaluation_period = serializers.CharField(required=True, max_length=50)
    reason = serializers.CharField(required=True, max_length=5000)
    attachment = serializers.FileField(required=False, allow_null=True)

    def validate_evaluation_score(self, value):
        if value >= 60:
            raise serializers.ValidationError(
                "Performance warning only issued for scores < 60%"
            )
        return value


class WarningAcknowledgeSerializer(serializers.Serializer):
    """
    Serializer for employee acknowledging warning
    Xodim ogohlantirishni tan olish serializeri
    """
    employee_response = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000
    )


class WarningResolveSerializer(serializers.Serializer):
    """
    Serializer for resolving warning
    Ogohlantirishni hal qilish serializeri
    """
    resolution_notes = serializers.CharField(required=True, max_length=2000)

    def validate_resolution_notes(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Resolution notes must be at least 10 characters long"
            )
        return value


class WarningEscalateSerializer(serializers.Serializer):
    """
    Serializer for escalating warning to termination
    Ogohlantirishni tugatishga kuchaytirish serializeri
    """
    termination_reason = serializers.CharField(required=True, max_length=5000)

    def validate_termination_reason(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Termination reason must be at least 20 characters long"
            )
        return value