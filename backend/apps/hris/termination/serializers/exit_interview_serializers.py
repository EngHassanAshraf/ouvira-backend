"""
Exit Interview Serializers / Chiqish Suhbati Serializerlari

Serializers for exit interviews
Chiqish suhbatlari uchun serializerlar
"""

from rest_framework import serializers
from apps.hris.termination.models import ExitInterview, TerminationRequest


class ExitInterviewListSerializer(serializers.ModelSerializer):
    """
    List serializer for exit interviews
    Chiqish suhbatlari ro'yxati serializeri
    """
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    interview_method_display = serializers.CharField(source='get_interview_method_display', read_only=True)
    primary_reason_display = serializers.CharField(source='get_primary_reason_display', read_only=True, allow_null=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = ExitInterview
        fields = [
            'id',
            'employee',
            'employee_name',
            'termination_request',
            'status',
            'status_display',
            'scheduled_date',
            'conducted_date',
            'interview_method',
            'interview_method_display',
            'primary_reason',
            'primary_reason_display',
            'overall_satisfaction',
            'is_overdue',
            'created_at'
        ]


class ExitInterviewDetailSerializer(serializers.ModelSerializer):
    """
    Detail serializer for exit interviews
    Chiqish suhbatlari tafsilot serializeri
    """
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_position = serializers.CharField(source='employee.position.name', read_only=True)
    employee_department = serializers.CharField(source='employee.department.name', read_only=True)

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    interview_method_display = serializers.CharField(source='get_interview_method_display', read_only=True)
    primary_reason_display = serializers.CharField(source='get_primary_reason_display', read_only=True, allow_null=True)

    conducted_by_name = serializers.CharField(source='conducted_by.full_name', read_only=True, allow_null=True)

    average_satisfaction = serializers.DecimalField(
        max_digits=3,
        decimal_places=2,
        read_only=True,
        allow_null=True
    )
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = ExitInterview
        fields = [
            'id',
            # Employee & Termination
            'employee',
            'employee_name',
            'employee_position',
            'employee_department',
            'termination_request',
            'status',
            'status_display',
            # Scheduling
            'scheduled_date',
            'conducted_date',
            'conducted_by',
            'conducted_by_name',
            'interview_method',
            'interview_method_display',
            'location',
            # Primary reason
            'primary_reason',
            'primary_reason_display',
            'reason_details',
            # Satisfaction ratings
            'overall_satisfaction',
            'job_satisfaction',
            'manager_satisfaction',
            'team_satisfaction',
            'compensation_satisfaction',
            'work_environment_satisfaction',
            'average_satisfaction',
            # Open-ended feedback
            'what_did_you_like',
            'what_to_improve',
            'would_recommend',
            'would_return',
            'additional_comments',
            # Internal
            'hr_notes',
            'action_items',
            'is_confidential',
            # Properties
            'is_overdue',
            # Timestamps
            'created_at',
            'updated_at'
        ]


class ExitInterviewScheduleSerializer(serializers.Serializer):
    """
    Serializer for scheduling exit interview
    Chiqish suhbatini rejalashtirish serializeri
    """
    termination_request = serializers.PrimaryKeyRelatedField(
        queryset=TerminationRequest.objects.filter(is_deleted=False)
    )
    scheduled_date = serializers.DateTimeField(required=True)
    interview_method = serializers.ChoiceField(
        choices=[
            ('in_person', 'In Person'),
            ('video_call', 'Video Call'),
            ('phone', 'Phone'),
            ('written', 'Written Form')
        ],
        default='in_person'
    )
    location = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200
    )


class ExitInterviewConductSerializer(serializers.Serializer):
    """
    Serializer for conducting exit interview
    Chiqish suhbatini o'tkazish serializeri
    """
    primary_reason = serializers.ChoiceField(
        choices=[
            ('better_opportunity', 'Better Opportunity'),
            ('salary', 'Salary/Compensation'),
            ('career_growth', 'Career Growth'),
            ('work_life_balance', 'Work-Life Balance'),
            ('management', 'Management Issues'),
            ('work_environment', 'Work Environment'),
            ('location', 'Location/Commute'),
            ('personal', 'Personal Reasons'),
            ('retirement', 'Retirement'),
            ('health', 'Health Reasons'),
            ('relocation', 'Relocation'),
            ('other', 'Other')
        ]
    )
    reason_details = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=5000
    )

    # Satisfaction ratings (1-5)
    overall_satisfaction = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=5
    )
    job_satisfaction = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=5
    )
    manager_satisfaction = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=5
    )
    team_satisfaction = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=5
    )
    compensation_satisfaction = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=5
    )
    work_environment_satisfaction = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=5
    )

    # Open-ended questions
    what_did_you_like = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000
    )
    what_to_improve = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000
    )
    would_recommend = serializers.BooleanField(required=False, allow_null=True)
    would_return = serializers.BooleanField(required=False, allow_null=True)
    additional_comments = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000
    )

    # HR internal
    hr_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000
    )
    action_items = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000
    )


class ExitInterviewRescheduleSerializer(serializers.Serializer):
    """
    Serializer for rescheduling exit interview
    Chiqish suhbatini qayta rejalashtirish serializeri
    """
    new_scheduled_date = serializers.DateTimeField(required=True)
    reschedule_reason = serializers.CharField(required=True, max_length=500)
    new_location = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200
    )


class ExitInterviewCancelSerializer(serializers.Serializer):
    """
    Serializer for cancelling exit interview
    Chiqish suhbatini bekor qilish serializeri
    """
    cancellation_reason = serializers.CharField(required=True, max_length=500)


class ExitInterviewNoShowSerializer(serializers.Serializer):
    """
    Serializer for marking exit interview as no-show
    Chiqish suhbatini kelmagan deb belgilash serializeri
    """
    no_show_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )
