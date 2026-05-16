"""
Termination Module Admin Configuration
"""

from django.contrib import admin
from .models import (
    TerminationRequest,
    TerminationWarning,
    ExitInterview,
    TerminationSettlement
)


@admin.register(TerminationRequest)
class TerminationRequestAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'termination_type',
        'status',
        'submission_date',
        'final_working_day',
        'is_voluntary'
    )
    list_filter = (
        'termination_type',
        'status',
        'is_voluntary',
        'submission_date'
    )
    search_fields = (
        'employee__first_name',
        'employee__last_name',
        'reason'
    )
    date_hierarchy = 'submission_date'
    readonly_fields = (
        'created_at',
        'updated_at',
        'manager_approval_date',
        'gm_approval_date',
        'processed_date'
    )

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'employee',
                'termination_type',
                'status',
                'is_voluntary',
                'reason'
            )
        }),
        ('Dates', {
            'fields': (
                'submission_date',
                'final_working_day',
                'notice_period_days'
            )
        }),
        ('Approvals', {
            'fields': (
                'requested_by',
                'approved_by_manager',
                'manager_approval_date',
                'approved_by_gm',
                'gm_approval_date'
            )
        }),
        ('Processing', {
            'fields': (
                'processed_by',
                'processed_date',
                'notes',
                'attachment'
            )
        }),
        ('Withdrawal', {
            'fields': (
                'withdrawal_request_date',
                'withdrawal_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(TerminationWarning)
class TerminationWarningAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'warning_type',
        'warning_level',
        'status',
        'issue_date',
        'absence_days_count'
    )
    list_filter = (
        'warning_type',
        'warning_level',
        'status',
        'issue_date'
    )
    search_fields = (
        'employee__first_name',
        'employee__last_name',
        'reason'
    )
    date_hierarchy = 'issue_date'
    readonly_fields = (
        'created_at',
        'updated_at',
        'acknowledged_date',
        'resolved_date',
        'escalation_date'
    )


@admin.register(ExitInterview)
class ExitInterviewAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'scheduled_date',
        'status',
        'primary_reason',
        'overall_satisfaction',
        'conducted_by'
    )
    list_filter = (
        'status',
        'primary_reason',
        'overall_satisfaction',
        'scheduled_date'
    )
    search_fields = (
        'employee__first_name',
        'employee__last_name',
        'reason_details'
    )
    date_hierarchy = 'scheduled_date'
    readonly_fields = (
        'created_at',
        'updated_at',
        'conducted_date'
    )

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'termination_request',
                'employee',
                'status'
            )
        }),
        ('Scheduling', {
            'fields': (
                'scheduled_date',
                'conducted_date',
                'conducted_by',
                'interview_method',
                'location'
            )
        }),
        ('Feedback', {
            'fields': (
                'primary_reason',
                'reason_details',
                'overall_satisfaction',
                'job_satisfaction',
                'manager_satisfaction',
                'team_satisfaction',
                'compensation_satisfaction',
                'work_environment_satisfaction'
            )
        }),
        ('Open-ended Questions', {
            'fields': (
                'what_did_you_like',
                'what_to_improve',
                'would_recommend',
                'would_return',
                'additional_comments'
            )
        }),
        ('Internal Notes', {
            'fields': (
                'hr_notes',
                'action_items',
                'is_confidential'
            ),
            'classes': ('collapse',)
        })
    )


@admin.register(TerminationSettlement)
class TerminationSettlementAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'status',
        'gross_amount',
        'total_deductions',
        'net_amount',
        'payment_date'
    )
    list_filter = (
        'status',
        'payment_method',
        'payment_date'
    )
    search_fields = (
        'employee__first_name',
        'employee__last_name',
        'payment_reference'
    )
    date_hierarchy = 'payment_date'
    readonly_fields = (
        'created_at',
        'updated_at',
        'gross_amount',
        'total_deductions',
        'net_amount',
        'calculated_date',
        'approved_date'
    )

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'termination_request',
                'employee',
                'status'
            )
        }),
        ('Settlement Components', {
            'fields': (
                'years_of_service',
                'end_of_service_benefit',
                'unused_leave_days',
                'unused_leave_amount',
                'pending_salary_days',
                'pending_salary_amount',
                'pending_bonus',
                'other_allowances'
            )
        }),
        ('Deductions', {
            'fields': (
                'advance_payments',
                'loan_balance',
                'other_deductions',
                'deduction_notes'
            )
        }),
        ('Totals (Auto-calculated)', {
            'fields': (
                'gross_amount',
                'total_deductions',
                'net_amount'
            )
        }),
        ('Calculation', {
            'fields': (
                'calculated_by',
                'calculated_date',
                'calculation_notes'
            )
        }),
        ('Approval', {
            'fields': (
                'approved_by',
                'approved_date'
            )
        }),
        ('Payment', {
            'fields': (
                'payment_date',
                'payment_method',
                'payment_reference',
                'paid_by'
            )
        }),
        ('Deceased Employee', {
            'fields': (
                'paid_to_heir',
                'heir_relationship',
                'heir_identification'
            ),
            'classes': ('collapse',)
        })
    )