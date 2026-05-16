"""
Termination Selectors / Tugatish Tanlash Funksiyalari

Read-only database queries for termination data
Tugatish ma'lumotlari uchun faqat o'qiladigan ma'lumotlar bazasi so'rovlari
"""

from django.db.models import Q, Count, Avg, Sum, F
from django.utils import timezone
from datetime import timedelta

from apps.hris.termination.models import (
    TerminationRequest,
    TerminationWarning,
    ExitInterview,
    TerminationSettlement
)


class TerminationSelector:
    """
    Selector for all termination-related queries
    Barcha tugatish bilan bog'liq so'rovlar uchun tanlovchi
    """

    # ========== TERMINATION REQUESTS ==========

    @staticmethod
    def get_employee_termination_requests(employee, include_deleted=False):
        """
        Get all termination requests for an employee
        Xodim uchun barcha tugatish so'rovlarini olish

        Args:
            employee: Employee object
            include_deleted: Include soft-deleted records

        Returns:
            QuerySet of TerminationRequest
        """
        queryset = TerminationRequest.objects.filter(employee=employee)

        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)

        return queryset.select_related(
            'employee',
            'requested_by',
            'approved_by_manager',
            'approved_by_gm',
            'rejected_by',
            'processed_by'
        ).order_by('-created_at')

    @staticmethod
    def get_active_resignation(employee):
        """
        Get employee's active resignation (if exists)
        Xodimning faol iste'fosini olish (mavjud bo'lsa)

        Args:
            employee: Employee object

        Returns:
            TerminationRequest or None
        """
        return TerminationRequest.objects.filter(
            employee=employee,
            termination_type=TerminationRequest.TerminationType.RESIGNATION,
            status__in=[
                TerminationRequest.Status.DRAFT,
                TerminationRequest.Status.SUBMITTED,
                TerminationRequest.Status.MANAGER_APPROVED,
                TerminationRequest.Status.GM_APPROVED
            ],
            is_deleted=False
        ).select_related('employee', 'requested_by').first()

    @staticmethod
    def get_pending_resignations_for_manager(manager, company=None):
        """
        Get resignations pending manager approval
        Menejer tasdiqini kutayotgan iste'folarni olish

        Args:
            manager: Manager employee object
            company: Optional company filter

        Returns:
            QuerySet of TerminationRequest
        """
        queryset = TerminationRequest.objects.filter(
            termination_type=TerminationRequest.TerminationType.RESIGNATION,
            status=TerminationRequest.Status.SUBMITTED,
            is_deleted=False
        )

        # TODO: Add manager hierarchy check
        # TODO: Menejer ierarxiyasi tekshiruvini qo'shish
        # queryset = queryset.filter(employee__manager=manager)

        if company:
            queryset = queryset.filter(employee__company=company)

        return queryset.select_related(
            'employee',
            'requested_by'
        ).order_by('submission_date')

    @staticmethod
    def get_pending_resignations_for_gm(company=None):
        """
        Get resignations pending GM approval
        GM tasdiqini kutayotgan iste'folarni olish

        Args:
            company: Optional company filter

        Returns:
            QuerySet of TerminationRequest
        """
        queryset = TerminationRequest.objects.filter(
            termination_type=TerminationRequest.TerminationType.RESIGNATION,
            status=TerminationRequest.Status.MANAGER_APPROVED,
            is_deleted=False
        )

        if company:
            queryset = queryset.filter(employee__company=company)

        return queryset.select_related(
            'employee',
            'requested_by',
            'approved_by_manager'
        ).order_by('manager_approval_date')

    @staticmethod
    def get_company_termination_requests(
            company,
            termination_type=None,
            status=None,
            start_date=None,
            end_date=None
    ):
        """
        Get all termination requests for a company with filters
        Kompaniya uchun barcha tugatish so'rovlarini filtrlar bilan olish

        Args:
            company: Company object
            termination_type: Filter by type (optional)
            status: Filter by status (optional)
            start_date: Filter by submission date >= (optional)
            end_date: Filter by submission date <= (optional)

        Returns:
            QuerySet of TerminationRequest
        """
        queryset = TerminationRequest.objects.filter(
            employee__company=company,
            is_deleted=False
        )

        if termination_type:
            queryset = queryset.filter(termination_type=termination_type)

        if status:
            queryset = queryset.filter(status=status)

        if start_date:
            queryset = queryset.filter(submission_date__gte=start_date)

        if end_date:
            queryset = queryset.filter(submission_date__lte=end_date)

        return queryset.select_related(
            'employee',
            'requested_by',
            'approved_by_manager',
            'approved_by_gm'
        ).order_by('-submission_date')

    @staticmethod
    def get_termination_detail(termination_id):
        """
        Get termination request with all related data
        Barcha bog'liq ma'lumotlar bilan tugatish so'rovini olish

        Args:
            termination_id: TerminationRequest ID

        Returns:
            TerminationRequest object or None
        """
        try:
            return TerminationRequest.objects.select_related(
                'employee',
                'requested_by',
                'approved_by_manager',
                'approved_by_gm',
                'rejected_by',
                'processed_by'
            ).prefetch_related(
                'warnings',
                'exit_interview',
                'settlement'
            ).get(id=termination_id, is_deleted=False)
        except TerminationRequest.DoesNotExist:
            return None

    # ========== WARNINGS ==========

    @staticmethod
    def get_employee_warnings(employee, warning_type=None, status=None):
        """
        Get warnings for an employee
        Xodim uchun ogohlantirishlarni olish

        Args:
            employee: Employee object
            warning_type: Filter by type (optional)
            status: Filter by status (optional)

        Returns:
            QuerySet of TerminationWarning
        """
        queryset = TerminationWarning.objects.filter(
            employee=employee,
            is_deleted=False
        )

        if warning_type:
            queryset = queryset.filter(warning_type=warning_type)

        if status:
            queryset = queryset.filter(status=status)

        return queryset.select_related(
            'employee',
            'issued_by',
            'escalated_to_termination'
        ).order_by('-issue_date')

    @staticmethod
    def get_active_warnings(company, warning_type=None):
        """
        Get all active warnings for a company
        Kompaniya uchun barcha faol ogohlantirishlarni olish

        Args:
            company: Company object
            warning_type: Filter by type (optional)

        Returns:
            QuerySet of TerminationWarning
        """
        queryset = TerminationWarning.objects.filter(
            employee__company=company,
            status__in=[
                TerminationWarning.Status.ISSUED,
                TerminationWarning.Status.ACKNOWLEDGED
            ],
            is_deleted=False
        )

        if warning_type:
            queryset = queryset.filter(warning_type=warning_type)

        return queryset.select_related(
            'employee',
            'issued_by'
        ).order_by('-issue_date')

    @staticmethod
    def get_final_warnings_for_escalation(company):
        """
        Get final warnings (2nd level) that can be escalated
        Kuchaytirilishi mumkin bo'lgan yakuniy ogohlantirishlarni olish (2-daraja)

        Args:
            company: Company object

        Returns:
            QuerySet of TerminationWarning
        """
        return TerminationWarning.objects.filter(
            employee__company=company,
            warning_level=TerminationWarning.WarningLevel.SECOND,
            status=TerminationWarning.Status.ISSUED,
            escalated_to_termination__isnull=True,
            is_deleted=False
        ).select_related(
            'employee',
            'issued_by'
        ).order_by('issue_date')

    # ========== EXIT INTERVIEWS ==========

    @staticmethod
    def get_scheduled_exit_interviews(company, start_date=None, end_date=None):
        """
        Get scheduled exit interviews
        Rejalashtirilgan chiqish suhbatlarini olish

        Args:
            company: Company object
            start_date: Filter by scheduled date >= (optional)
            end_date: Filter by scheduled date <= (optional)

        Returns:
            QuerySet of ExitInterview
        """
        queryset = ExitInterview.objects.filter(
            employee__company=company,
            status=ExitInterview.Status.SCHEDULED,
            is_deleted=False
        )

        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)

        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)

        return queryset.select_related(
            'employee',
            'termination_request'
        ).order_by('scheduled_date')

    @staticmethod
    def get_completed_exit_interviews(company, start_date=None, end_date=None):
        """
        Get completed exit interviews
        Tugallangan chiqish suhbatlarini olish

        Args:
            company: Company object
            start_date: Filter by conducted date >= (optional)
            end_date: Filter by conducted date <= (optional)

        Returns:
            QuerySet of ExitInterview
        """
        queryset = ExitInterview.objects.filter(
            employee__company=company,
            status=ExitInterview.Status.COMPLETED,
            is_deleted=False
        )

        if start_date:
            queryset = queryset.filter(conducted_date__gte=start_date)

        if end_date:
            queryset = queryset.filter(conducted_date__lte=end_date)

        return queryset.select_related(
            'employee',
            'termination_request',
            'conducted_by'
        ).order_by('-conducted_date')

    @staticmethod
    def get_overdue_exit_interviews(company):
        """
        Get overdue scheduled exit interviews
        Muddati o'tgan rejalashtirilgan chiqish suhbatlarini olish

        Args:
            company: Company object

        Returns:
            QuerySet of ExitInterview
        """
        return ExitInterview.objects.filter(
            employee__company=company,
            status=ExitInterview.Status.SCHEDULED,
            scheduled_date__lt=timezone.now(),
            is_deleted=False
        ).select_related(
            'employee',
            'termination_request'
        ).order_by('scheduled_date')

    # ========== SETTLEMENTS ==========

    @staticmethod
    def get_pending_settlements(company):
        """
        Get settlements pending approval
        Tasdiqni kutayotgan hisob-kitoblarni olish

        Args:
            company: Company object

        Returns:
            QuerySet of TerminationSettlement
        """
        return TerminationSettlement.objects.filter(
            employee__company=company,
            status__in=[
                TerminationSettlement.Status.PENDING,
                TerminationSettlement.Status.CALCULATED
            ],
            is_deleted=False
        ).select_related(
            'employee',
            'termination_request',
            'calculated_by'
        ).order_by('calculated_date')

    @staticmethod
    def get_approved_settlements_for_payment(company):
        """
        Get approved settlements ready for payment
        To'lov uchun tayyor tasdiqlangan hisob-kitoblarni olish

        Args:
            company: Company object

        Returns:
            QuerySet of TerminationSettlement
        """
        return TerminationSettlement.objects.filter(
            employee__company=company,
            status=TerminationSettlement.Status.APPROVED,
            is_deleted=False
        ).select_related(
            'employee',
            'termination_request',
            'approved_by'
        ).order_by('approved_date')

    @staticmethod
    def get_paid_settlements(company, start_date=None, end_date=None):
        """
        Get paid settlements
        To'langan hisob-kitoblarni olish

        Args:
            company: Company object
            start_date: Filter by payment date >= (optional)
            end_date: Filter by payment date <= (optional)

        Returns:
            QuerySet of TerminationSettlement
        """
        queryset = TerminationSettlement.objects.filter(
            employee__company=company,
            status=TerminationSettlement.Status.PAID,
            is_deleted=False
        )

        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)

        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)

        return queryset.select_related(
            'employee',
            'termination_request',
            'paid_by'
        ).order_by('-payment_date')

    # ========== ANALYTICS & REPORTS ==========

    @staticmethod
    def get_termination_statistics(company, start_date=None, end_date=None):
        """
        Get termination statistics for company
        Kompaniya uchun tugatish statistikasini olish

        Args:
            company: Company object
            start_date: Start date for period (optional)
            end_date: End date for period (optional)

        Returns:
            Dict with statistics
        """
        queryset = TerminationRequest.objects.filter(
            employee__company=company,
            is_deleted=False
        )

        if start_date:
            queryset = queryset.filter(submission_date__gte=start_date)

        if end_date:
            queryset = queryset.filter(submission_date__lte=end_date)

        # Total counts by type
        # Tur bo'yicha umumiy sonlar
        by_type = queryset.values('termination_type').annotate(
            count=Count('id')
        ).order_by('-count')

        # Total counts by status
        # Holat bo'yicha umumiy sonlar
        by_status = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('-count')

        # Resignation specific stats
        # Iste'foga xos statistika
        resignations = queryset.filter(
            termination_type=TerminationRequest.TerminationType.RESIGNATION
        )

        withdrawn_resignations = resignations.filter(
            status=TerminationRequest.Status.WITHDRAWN
        ).count()

        return {
            'total_terminations': queryset.count(),
            'by_type': list(by_type),
            'by_status': list(by_status),
            'total_resignations': resignations.count(),
            'withdrawn_resignations': withdrawn_resignations,
            'withdrawal_rate': (
                (withdrawn_resignations / resignations.count() * 100)
                if resignations.count() > 0 else 0
            )
        }

    @staticmethod
    def get_exit_interview_insights(company, start_date=None, end_date=None):
        """
        Get insights from exit interviews
        Chiqish suhbatlaridan tushunchalar olish

        Args:
            company: Company object
            start_date: Start date for period (optional)
            end_date: End date for period (optional)

        Returns:
            Dict with insights
        """
        queryset = ExitInterview.objects.filter(
            employee__company=company,
            status=ExitInterview.Status.COMPLETED,
            is_deleted=False
        )

        if start_date:
            queryset = queryset.filter(conducted_date__gte=start_date)

        if end_date:
            queryset = queryset.filter(conducted_date__lte=end_date)

        # Reasons for leaving
        # Ketish sabablari
        by_reason = queryset.values('primary_reason').annotate(
            count=Count('id')
        ).order_by('-count')

        # Average satisfaction scores
        # O'rtacha qoniqish ballari
        avg_satisfaction = queryset.aggregate(
            overall=Avg('overall_satisfaction'),
            job=Avg('job_satisfaction'),
            manager=Avg('manager_satisfaction'),
            team=Avg('team_satisfaction'),
            compensation=Avg('compensation_satisfaction'),
            work_environment=Avg('work_environment_satisfaction')
        )

        # Recommendation rate
        # Tavsiya etish darajasi
        total_completed = queryset.count()
        would_recommend = queryset.filter(would_recommend=True).count()
        would_return = queryset.filter(would_return=True).count()

        return {
            'total_interviews': total_completed,
            'by_reason': list(by_reason),
            'average_satisfaction': avg_satisfaction,
            'would_recommend_count': would_recommend,
            'would_recommend_rate': (
                (would_recommend / total_completed * 100)
                if total_completed > 0 else 0
            ),
            'would_return_count': would_return,
            'would_return_rate': (
                (would_return / total_completed * 100)
                if total_completed > 0 else 0
            )
        }

    @staticmethod
    def get_settlement_summary(company, start_date=None, end_date=None):
        """
        Get settlement summary for company
        Kompaniya uchun hisob-kitob xulosasini olish

        Args:
            company: Company object
            start_date: Start date for period (optional)
            end_date: End date for period (optional)

        Returns:
            Dict with settlement summary
        """
        queryset = TerminationSettlement.objects.filter(
            employee__company=company,
            status=TerminationSettlement.Status.PAID,
            is_deleted=False
        )

        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)

        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)

        summary = queryset.aggregate(
            total_paid=Sum('net_amount'),
            total_gratuity=Sum('end_of_service_benefit'),
            total_leave_payout=Sum('unused_leave_amount'),
            total_deductions=Sum('total_deductions'),
            count=Count('id')
        )

        return summary