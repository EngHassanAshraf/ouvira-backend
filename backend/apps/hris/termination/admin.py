"""
Termination Module Admin Configuration
Enhanced with actions, inlines, custom filters and display methods
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from datetime import date, timedelta

from .models import (
    TerminationRequest,
    TerminationWarning,
    ExitInterview,
    TerminationSettlement
)


# ========== CUSTOM FILTERS ==========

class PendingManagerApprovalFilter(admin.SimpleListFilter):
    """Filter for resignations pending manager approval"""
    title = _('Pending Manager Approval')
    parameter_name = 'pending_manager'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Yes')),
            ('no', _('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(
                termination_type='resignation',
                status='submitted'
            )
        if self.value() == 'no':
            return queryset.exclude(
                termination_type='resignation',
                status='submitted'
            )


class PendingGMApprovalFilter(admin.SimpleListFilter):
    """Filter for resignations pending GM approval"""
    title = _('Pending GM Approval')
    parameter_name = 'pending_gm'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Yes')),
            ('no', _('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(
                termination_type='resignation',
                status='manager_approved'
            )
        if self.value() == 'no':
            return queryset.exclude(
                termination_type='resignation',
                status='manager_approved'
            )


class FinalWorkingDaySoonFilter(admin.SimpleListFilter):
    """Filter for terminations with final working day approaching"""
    title = _('Final Working Day')
    parameter_name = 'final_day'

    def lookups(self, request, model_admin):
        return (
            ('this_week', _('This Week')),
            ('this_month', _('This Month')),
            ('overdue', _('Overdue')),
        )

    def queryset(self, request, queryset):
        today = date.today()
        if self.value() == 'this_week':
            week_end = today + timedelta(days=7)
            return queryset.filter(
                final_working_day__gte=today,
                final_working_day__lte=week_end
            )
        if self.value() == 'this_month':
            month_end = today + timedelta(days=30)
            return queryset.filter(
                final_working_day__gte=today,
                final_working_day__lte=month_end
            )
        if self.value() == 'overdue':
            return queryset.filter(
                final_working_day__lt=today,
                status__in=['submitted', 'manager_approved', 'gm_approved']
            )


# ========== INLINE ADMINS ==========

class WarningInline(admin.TabularInline):
    """Inline display of warnings related to termination"""
    model = TerminationWarning
    extra = 0
    fields = ('warning_type', 'warning_level', 'status', 'issue_date', 'absence_days_count')
    readonly_fields = ('warning_type', 'warning_level', 'status', 'issue_date')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class SettlementInline(admin.StackedInline):
    """Inline display of settlement"""
    model = TerminationSettlement
    extra = 0
    fields = (
        ('status', 'gross_amount', 'total_deductions', 'net_amount'),
        ('payment_date', 'payment_method', 'payment_reference')
    )
    readonly_fields = ('gross_amount', 'total_deductions', 'net_amount')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class ExitInterviewInline(admin.StackedInline):
    """Inline display of exit interview"""
    model = ExitInterview
    extra = 0
    fields = (
        ('status', 'scheduled_date', 'conducted_date'),
        ('primary_reason', 'overall_satisfaction'),
        'would_recommend'
    )
    readonly_fields = ('status', 'scheduled_date', 'conducted_date')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# ========== MAIN ADMIN CLASSES ==========

@admin.register(TerminationRequest)
class TerminationRequestAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'termination_type_badge',
        'status_badge',
        'submission_date',
        'final_working_day',
        'days_remaining_display',
        'approval_progress',
        'has_warnings',
        'has_settlement_display',
        'has_exit_interview_display'
    )
    list_filter = (
        'termination_type',
        'status',
        'is_voluntary',
        PendingManagerApprovalFilter,
        PendingGMApprovalFilter,
        FinalWorkingDaySoonFilter,
        'submission_date'
    )
    search_fields = (
        'employee__first_name',
        'employee__last_name',
        'employee__employee_id',
        'reason'
    )
    date_hierarchy = 'submission_date'
    readonly_fields = (
        'created_at',
        'updated_at',
        'manager_approval_date',
        'gm_approval_date',
        'processed_date',
        'days_remaining_display'
    )

    # Inlines
    inlines = [WarningInline, SettlementInline, ExitInterviewInline]

    # Actions
    actions = ['mark_as_processed', 'cancel_selected']

    fieldsets = (
        ('📋 Basic Information', {
            'fields': (
                'employee',
                'termination_type',
                'status',
                'is_voluntary',
                'reason'
            )
        }),
        ('📅 Important Dates', {
            'fields': (
                'submission_date',
                'final_working_day',
                'notice_period_days',
                'days_remaining_display'
            )
        }),
        ('✅ Approvals', {
            'fields': (
                'requested_by',
                'approved_by_manager',
                'manager_approval_date',
                'approved_by_gm',
                'gm_approval_date'
            )
        }),
        ('⚙️ Processing', {
            'fields': (
                'processed_by',
                'processed_date',
                'notes',
                'attachment'
            )
        }),
        ('↩️ Withdrawal', {
            'fields': (
                'withdrawal_request_date',
                'withdrawal_reason'
            ),
            'classes': ('collapse',)
        }),
        ('🕐 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    # Custom display methods
    @admin.display(description='Type', ordering='termination_type')
    def termination_type_badge(self, obj):
        colors = {
            'resignation': '#2196F3',
            'behavioral': '#F44336',
            'performance': '#FF9800',
            'probation': '#9C27B0',
            'medical': '#4CAF50',
            'layoff': '#607D8B',
            'deceased': '#000000',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.termination_type, '#999'),
            obj.get_termination_type_display()
        )

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        colors = {
            'draft': '#9E9E9E',
            'submitted': '#2196F3',
            'manager_approved': '#FF9800',
            'gm_approved': '#4CAF50',
            'rejected': '#F44336',
            'withdrawn': '#795548',
            'processed': '#009688',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.status, '#999'),
            obj.get_status_display()
        )

    @admin.display(description='Days Remaining')
    def days_remaining_display(self, obj):
        days = obj.days_until_final_working_day
        if days is None:
            return '-'
        if days < 0:
            return format_html('<span style="color: red;">Overdue by {} days</span>', abs(days))
        if days == 0:
            return format_html('<span style="color: orange; font-weight: bold;">TODAY</span>')
        if days <= 7:
            return format_html('<span style="color: orange;">{} days</span>', days)
        return format_html('<span style="color: green;">{} days</span>', days)

    @admin.display(description='Approval Status')
    def approval_progress(self, obj):
        if obj.termination_type != 'resignation':
            return '-'

        icons = []
        if obj.approved_by_manager:
            icons.append('<span style="color: green;">✓ Manager</span>')
        else:
            icons.append('<span style="color: gray;">○ Manager</span>')

        if obj.approved_by_gm:
            icons.append('<span style="color: green;">✓ GM</span>')
        else:
            icons.append('<span style="color: gray;">○ GM</span>')

        return format_html(' | '.join(icons))

    @admin.display(description='Warnings', boolean=True)
    def has_warnings(self, obj):
        return obj.warnings.exists()

    @admin.display(description='Settlement', boolean=True)
    def has_settlement_display(self, obj):
        return hasattr(obj, 'settlement')

    @admin.display(description='Exit Interview', boolean=True)
    def has_exit_interview_display(self, obj):
        return hasattr(obj, 'exit_interview')

    # Actions
    @admin.action(description='Mark selected as Processed')
    def mark_as_processed(self, request, queryset):
        updated = queryset.filter(
            status='gm_approved'
        ).update(status='processed')
        self.message_user(request, f'{updated} terminations marked as processed.')

    @admin.action(description='Cancel selected terminations')
    def cancel_selected(self, request, queryset):
        updated = queryset.filter(
            status__in=['draft', 'submitted']
        ).update(status='withdrawn')
        self.message_user(request, f'{updated} terminations cancelled.')


@admin.register(TerminationWarning)
class TerminationWarningAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'warning_type_badge',
        'warning_level_badge',
        'status_badge',
        'issue_date',
        'absence_days_display',
        'evaluation_score_display',
        'can_escalate_display'
    )
    list_filter = (
        'warning_type',
        'warning_level',
        'status',
        'issue_date',
        'sent_via_registered_mail',
        'form_s6_attached'
    )
    search_fields = (
        'employee__first_name',
        'employee__last_name',
        'employee__employee_id',
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

    # Actions
    actions = ['mark_as_acknowledged', 'mark_as_resolved']

    fieldsets = (
        ('📋 Basic Information', {
            'fields': (
                'employee',
                'warning_type',
                'warning_level',
                'status',
                'reason',
                'issue_date'
            )
        }),
        ('⏰ Absence Details', {
            'fields': (
                'absence_start_date',
                'absence_days_count'
            ),
            'classes': ('collapse',)
        }),
        ('📊 Performance Details', {
            'fields': (
                'evaluation_score',
                'evaluation_period'
            ),
            'classes': ('collapse',)
        }),
        ('📬 Delivery', {
            'fields': (
                'sent_via_registered_mail',
                'registered_mail_tracking',
                'form_s6_attached'
            )
        }),
        ('✅ Acknowledgment & Resolution', {
            'fields': (
                'acknowledged_date',
                'employee_response',
                'resolved_date',
                'resolution_notes'
            )
        }),
        ('⚠️ Escalation', {
            'fields': (
                'escalated_to_termination',
                'escalation_date'
            )
        }),
        ('👤 Issued By', {
            'fields': ('issued_by',)
        }),
        ('📎 Attachment', {
            'fields': ('attachment',),
            'classes': ('collapse',)
        })
    )

    # Custom display methods
    @admin.display(description='Type', ordering='warning_type')
    def warning_type_badge(self, obj):
        colors = {
            'absence_egyptian': '#FF5722',
            'absence_saudi': '#E91E63',
            'performance': '#9C27B0',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.warning_type, '#999'),
            obj.get_warning_type_display()
        )

    @admin.display(description='Level', ordering='warning_level')
    def warning_level_badge(self, obj):
        if obj.warning_level == 'first':
            return format_html(
                '<span style="background-color: #FF9800; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">1st</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #F44336; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">2nd (FINAL)</span>'
            )

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        colors = {
            'issued': '#2196F3',
            'acknowledged': '#FF9800',
            'resolved': '#4CAF50',
            'escalated': '#F44336',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.status, '#999'),
            obj.get_status_display()
        )

    @admin.display(description='Absence Days')
    def absence_days_display(self, obj):
        if obj.absence_days_count:
            if obj.absence_days_count >= 10:
                return format_html('<span style="color: red; font-weight: bold;">{} days</span>',
                                   obj.absence_days_count)
            elif obj.absence_days_count >= 5:
                return format_html('<span style="color: orange;">{} days</span>',
                                   obj.absence_days_count)
            return f'{obj.absence_days_count} days'
        return '-'

    @admin.display(description='Evaluation Score')
    def evaluation_score_display(self, obj):
        if obj.evaluation_score:
            if obj.evaluation_score < 50:
                return format_html('<span style="color: red; font-weight: bold;">{}%</span>',
                                   obj.evaluation_score)
            elif obj.evaluation_score < 60:
                return format_html('<span style="color: orange;">{}%</span>',
                                   obj.evaluation_score)
            return f'{obj.evaluation_score}%'
        return '-'

    @admin.display(description='Can Escalate', boolean=True)
    def can_escalate_display(self, obj):
        return obj.can_escalate_to_termination

    # Actions
    @admin.action(description='Mark selected as Acknowledged')
    def mark_as_acknowledged(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='issued').update(
            status='acknowledged',
            acknowledged_date=timezone.now()
        )
        self.message_user(request, f'{updated} warnings marked as acknowledged.')

    @admin.action(description='Mark selected as Resolved')
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(
            status__in=['issued', 'acknowledged']
        ).update(
            status='resolved',
            resolved_date=timezone.now()
        )
        self.message_user(request, f'{updated} warnings marked as resolved.')


@admin.register(ExitInterview)
class ExitInterviewAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'scheduled_date',
        'status_badge',
        'primary_reason_display',
        'satisfaction_display',
        'would_recommend_display',
        'is_overdue_display'
    )
    list_filter = (
        'status',
        'interview_method',
        'primary_reason',
        'overall_satisfaction',
        'would_recommend',
        'scheduled_date'
    )
    search_fields = (
        'employee__first_name',
        'employee__last_name',
        'employee__employee_id',
        'reason_details'
    )
    date_hierarchy = 'scheduled_date'
    readonly_fields = (
        'created_at',
        'updated_at',
        'conducted_date',
        'satisfaction_display'
    )

    # Actions
    actions = ['mark_as_completed', 'mark_as_no_show']

    fieldsets = (
        ('📋 Basic Information', {
            'fields': (
                'termination_request',
                'employee',
                'status'
            )
        }),
        ('📅 Scheduling', {
            'fields': (
                'scheduled_date',
                'conducted_date',
                'conducted_by',
                'interview_method',
                'location'
            )
        }),
        ('💭 Feedback', {
            'fields': (
                'primary_reason',
                'reason_details',
                ('overall_satisfaction', 'job_satisfaction'),
                ('manager_satisfaction', 'team_satisfaction'),
                ('compensation_satisfaction', 'work_environment_satisfaction'),
                'satisfaction_display'
            )
        }),
        ('✍️ Open-ended Questions', {
            'fields': (
                'what_did_you_like',
                'what_to_improve',
                ('would_recommend', 'would_return'),
                'additional_comments'
            )
        }),
        ('🔒 Internal Notes', {
            'fields': (
                'hr_notes',
                'action_items',
                'is_confidential'
            ),
            'classes': ('collapse',)
        })
    )

    # Custom display methods
    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        colors = {
            'scheduled': '#2196F3',
            'completed': '#4CAF50',
            'cancelled': '#9E9E9E',
            'no_show': '#F44336',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.status, '#999'),
            obj.get_status_display()
        )

    @admin.display(description='Reason')
    def primary_reason_display(self, obj):
        if obj.primary_reason:
            return obj.get_primary_reason_display()
        return '-'

    @admin.display(description='Avg Satisfaction')
    def satisfaction_display(self, obj):
        avg = obj.average_satisfaction
        if avg is None:
            return '-'
        if avg >= 4:
            return format_html('<span style="color: green; font-weight: bold;">{:.1f}/5 ⭐</span>', avg)
        elif avg >= 3:
            return format_html('<span style="color: orange;">{:.1f}/5</span>', avg)
        else:
            return format_html('<span style="color: red;">{:.1f}/5</span>', avg)

    @admin.display(description='Would Recommend', boolean=True)
    def would_recommend_display(self, obj):
        return obj.would_recommend

    @admin.display(description='Overdue', boolean=True)
    def is_overdue_display(self, obj):
        return obj.is_overdue

    # Actions
    @admin.action(description='Mark selected as Completed')
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='scheduled').update(
            status='completed',
            conducted_date=timezone.now()
        )
        self.message_user(request, f'{updated} interviews marked as completed.')

    @admin.action(description='Mark selected as No Show')
    def mark_as_no_show(self, request, queryset):
        updated = queryset.filter(status='scheduled').update(status='no_show')
        self.message_user(request, f'{updated} interviews marked as no show.')


@admin.register(TerminationSettlement)
class TerminationSettlementAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'status_badge',
        'gross_amount_display',
        'deductions_display',
        'net_amount_display',
        'payment_date',
        'payment_method_display',
        'is_ready_display'
    )
    list_filter = (
        'status',
        'payment_method',
        'payment_date',
        'calculated_date'
    )
    search_fields = (
        'employee__first_name',
        'employee__last_name',
        'employee__employee_id',
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

    # Actions
    actions = ['mark_as_approved', 'mark_as_paid']

    fieldsets = (
        ('📋 Basic Information', {
            'fields': (
                'termination_request',
                'employee',
                'status'
            )
        }),
        ('💰 Settlement Components', {
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
        ('➖ Deductions', {
            'fields': (
                'advance_payments',
                'loan_balance',
                'other_deductions',
                'deduction_notes'
            )
        }),
        ('📊 Totals (Auto-calculated)', {
            'fields': (
                'gross_amount',
                'total_deductions',
                'net_amount'
            )
        }),
        ('🧮 Calculation', {
            'fields': (
                'calculated_by',
                'calculated_date',
                'calculation_notes'
            )
        }),
        ('✅ Approval', {
            'fields': (
                'approved_by',
                'approved_date'
            )
        }),
        ('💳 Payment', {
            'fields': (
                'payment_date',
                'payment_method',
                'payment_reference',
                'paid_by'
            )
        }),
        ('👥 Deceased Employee', {
            'fields': (
                'paid_to_heir',
                'heir_relationship',
                'heir_identification'
            ),
            'classes': ('collapse',)
        })
    )

    # Custom display methods
    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        colors = {
            'pending': '#9E9E9E',
            'calculated': '#2196F3',
            'approved': '#FF9800',
            'paid': '#4CAF50',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.status, '#999'),
            obj.get_status_display()
        )

    @admin.display(description='Gross Amount', ordering='gross_amount')
    def gross_amount_display(self, obj):
        return format_html('<span style="color: green; font-weight: bold;">${:,.2f}</span>',
                           obj.gross_amount or 0)

    @admin.display(description='Deductions', ordering='total_deductions')
    def deductions_display(self, obj):
        if obj.total_deductions and obj.total_deductions > 0:
            return format_html('<span style="color: red;">-${:,.2f}</span>',
                               obj.total_deductions)
        return '$0.00'

    @admin.display(description='Net Amount', ordering='net_amount')
    def net_amount_display(self, obj):
        return format_html('<span style="color: blue; font-weight: bold; font-size: 13px;">${:,.2f}</span>',
                           obj.net_amount or 0)

    @admin.display(description='Payment Method')
    def payment_method_display(self, obj):
        if obj.payment_method:
            return obj.get_payment_method_display()
        return '-'

    @admin.display(description='Ready for Payment', boolean=True)
    def is_ready_display(self, obj):
        return obj.is_ready_for_payment

    # Actions
    @admin.action(description='Mark selected as Approved')
    def mark_as_approved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='calculated').update(
            status='approved',
            approved_date=timezone.now(),
            approved_by=request.user.employee if hasattr(request.user, 'employee') else None
        )
        self.message_user(request, f'{updated} settlements marked as approved.')

    @admin.action(description='Mark selected as Paid')
    def mark_as_paid(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='approved').update(
            status='paid',
            payment_date=timezone.now().date(),
            paid_by=request.user.employee if hasattr(request.user, 'employee') else None
        )
        self.message_user(request, f'{updated} settlements marked as paid.')