"""
Settlement Service / Hisob-kitob Xizmati

Calculate and manage final settlements
Yakuniy hisob-kitoblarni hisoblash va boshqarish
"""

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.hris.termination.models import TerminationSettlement, TerminationRequest
from apps.audit.services import log_activity


class SettlementService:
    """
    Service for managing termination settlements
    Tugatish hisob-kitoblarini boshqarish xizmati
    """

    @staticmethod
    @transaction.atomic
    def create_settlement(
            termination_request,
            years_of_service,
            unused_leave_days,
            pending_salary_days,
            calculated_by,
            end_of_service_benefit=None,
            pending_bonus=Decimal("0.00"),
            other_allowances=Decimal("0.00"),
            advance_payments=Decimal("0.00"),
            loan_balance=Decimal("0.00"),
            other_deductions=Decimal("0.00"),
            deduction_notes="",
            calculation_notes=""
    ):
        """
        Create settlement for termination
        Tugatish uchun hisob-kitob yaratish

        Args:
            termination_request: TerminationRequest object
            years_of_service: Total years worked
            unused_leave_days: Unused leave balance
            pending_salary_days: Days worked in final month
            calculated_by: HR calculating
            end_of_service_benefit: Gratuity amount (auto-calculated if None)
            pending_bonus: Any pending bonuses
            other_allowances: Housing, transport, etc.
            advance_payments: Salary advances to deduct
            loan_balance: Outstanding loans
            other_deductions: Other deductions
            deduction_notes: Details of deductions
            calculation_notes: Methodology notes

        Returns:
            TerminationSettlement object
        """

        # Check if settlement already exists
        # Hisob-kitob allaqachon mavjudligini tekshirish
        if hasattr(termination_request, 'settlement'):
            raise ValidationError(
                f"Settlement already exists for this termination (ID: {termination_request.settlement.id})"
            )

        # Get employee salary (TODO: integrate with payroll module)
        # Xodim maoshini olish (TODO: maosh moduli bilan integratsiya)
        # For now, we'll use a placeholder
        # Hozircha, to'ldiruvchi ishlatamiz
        monthly_salary = Decimal("5000.00")  # TODO: Get from employee.salary
        daily_salary = monthly_salary / Decimal("30")

        # Calculate end-of-service benefit if not provided
        # Agar berilmagan bo'lsa, xizmat yakuni to'lovini hisoblash
        if end_of_service_benefit is None:
            # Saudi Arabia gratuity calculation example:
            # Saudiya Arabistoni gratuity hisoblash misoli:
            # - Half month salary per year for first 5 years
            # - Full month salary per year for years after 5
            # - Birinchi 5 yil uchun oylik maoshning yarmini
            # - 5 yildan keyin har bir yil uchun to'liq oylik maosh

            if years_of_service <= 5:
                end_of_service_benefit = (monthly_salary / 2) * Decimal(str(years_of_service))
            else:
                first_five_years = (monthly_salary / 2) * Decimal("5")
                remaining_years = Decimal(str(years_of_service)) - Decimal("5")
                end_of_service_benefit = first_five_years + (monthly_salary * remaining_years)

        # Calculate unused leave amount
        # Ishlatilmagan ta'til miqdorini hisoblash
        unused_leave_amount = daily_salary * Decimal(str(unused_leave_days))

        # Calculate pending salary amount
        # To'lanmagan maosh miqdorini hisoblash
        pending_salary_amount = daily_salary * Decimal(str(pending_salary_days))

        # Create settlement
        # Hisob-kitob yaratish
        settlement = TerminationSettlement.objects.create(
            termination_request=termination_request,
            employee=termination_request.employee,
            status=TerminationSettlement.Status.CALCULATED,
            years_of_service=Decimal(str(years_of_service)),
            end_of_service_benefit=end_of_service_benefit,
            unused_leave_days=Decimal(str(unused_leave_days)),
            unused_leave_amount=unused_leave_amount,
            pending_salary_days=Decimal(str(pending_salary_days)),
            pending_salary_amount=pending_salary_amount,
            pending_bonus=pending_bonus,
            other_allowances=other_allowances,
            advance_payments=advance_payments,
            loan_balance=loan_balance,
            other_deductions=other_deductions,
            deduction_notes=deduction_notes,
            calculated_by=calculated_by,
            calculation_notes=calculation_notes
        )

        # Totals are auto-calculated in model.save()
        # Jami model.save() da avtomatik hisoblanadi

        # Log activity
        log_activity(
            user=calculated_by,
            action="SETTLEMENT_CALCULATED",
            model_name="TerminationSettlement",
            object_id=settlement.id,
            changes={
                "employee": termination_request.employee.full_name,
                "gross_amount": float(settlement.gross_amount),
                "net_amount": float(settlement.net_amount)
            }
        )

        return settlement

    @staticmethod
    @transaction.atomic
    def approve_settlement(settlement, approved_by):
        """
        Approve settlement for payment
        To'lov uchun hisob-kitobni tasdiqlash

        Args:
            settlement: TerminationSettlement object
            approved_by: Manager/GM approving

        Returns:
            Updated TerminationSettlement
        """

        # Validate status
        # Holatni tekshirish
        if settlement.status != TerminationSettlement.Status.CALCULATED:
            raise ValidationError(
                f"Can only approve settlements in CALCULATED status. Current: {settlement.get_status_display()}"
            )

        # Update settlement
        # Hisob-kitobni yangilash
        settlement.status = TerminationSettlement.Status.APPROVED
        settlement.approved_by = approved_by
        settlement.save()

        # Log activity
        log_activity(
            user=approved_by,
            action="SETTLEMENT_APPROVED",
            model_name="TerminationSettlement",
            object_id=settlement.id,
            changes={
                "employee": settlement.employee.full_name,
                "approved_date": str(settlement.approved_date),
                "net_amount": float(settlement.net_amount)
            }
        )

        return settlement

    @staticmethod
    @transaction.atomic
    def process_payment(
            settlement,
            payment_date,
            payment_method,
            payment_reference,
            paid_by,
            paid_to_heir=None,
            heir_relationship=None,
            heir_identification=None
    ):
        """
        Process payment for settlement
        Hisob-kitob uchun to'lovni qayta ishlash

        Args:
            settlement: TerminationSettlement object
            payment_date: Date of payment
            payment_method: bank_transfer, check, or cash
            payment_reference: Transaction ID or check number
            paid_by: Finance processing payment
            paid_to_heir: Heir name (for deceased employees)
            heir_relationship: Relationship to deceased
            heir_identification: Heir ID number

        Returns:
            Updated TerminationSettlement
        """

        # Validate status
        # Holatni tekshirish
        if settlement.status != TerminationSettlement.Status.APPROVED:
            raise ValidationError(
                f"Can only pay approved settlements. Current: {settlement.get_status_display()}"
            )

        # Validate payment method
        # To'lov usulini tekshirish
        valid_methods = ['bank_transfer', 'check', 'cash']
        if payment_method not in valid_methods:
            raise ValidationError(
                f"Invalid payment method. Must be one of: {valid_methods}"
            )

        # For deceased employees, heir information is required
        # Vafot etgan xodimlar uchun merosxo'r ma'lumoti talab qilinadi
        if settlement.termination_request.termination_type == TerminationRequest.TerminationType.DECEASED:
            if not paid_to_heir or not heir_relationship:
                raise ValidationError(
                    "Heir information required for deceased employee settlements"
                )

        # Update settlement
        # Hisob-kitobni yangilash
        settlement.status = TerminationSettlement.Status.PAID
        settlement.payment_date = payment_date
        settlement.payment_method = payment_method
        settlement.payment_reference = payment_reference
        settlement.paid_by = paid_by

        if paid_to_heir:
            settlement.paid_to_heir = paid_to_heir
            settlement.heir_relationship = heir_relationship or ""
            settlement.heir_identification = heir_identification or ""

        settlement.save()

        # Log activity
        log_activity(
            user=paid_by,
            action="SETTLEMENT_PAID",
            model_name="TerminationSettlement",
            object_id=settlement.id,
            changes={
                "employee": settlement.employee.full_name,
                "payment_date": str(payment_date),
                "payment_method": payment_method,
                "net_amount": float(settlement.net_amount),
                "paid_to_heir": paid_to_heir
            }
        )

        return settlement

    @staticmethod
    @transaction.atomic
    def adjust_settlement(
            settlement,
            adjusted_by,
            adjustment_reason,
            **updated_fields
    ):
        """
        Adjust settlement before approval
        Tasdiqdan oldin hisob-kitobni sozlash

        Args:
            settlement: TerminationSettlement object
            adjusted_by: HR adjusting
            adjustment_reason: Reason for adjustment
            **updated_fields: Fields to update (e.g., pending_bonus=500)

        Returns:
            Updated TerminationSettlement
        """

        # Validate status
        # Holatni tekshirish
        if settlement.status not in [
            TerminationSettlement.Status.PENDING,
            TerminationSettlement.Status.CALCULATED
        ]:
            raise ValidationError(
                f"Cannot adjust settlement in status: {settlement.get_status_display()}"
            )

        if not adjustment_reason:
            raise ValidationError("Adjustment reason is required")

        # Track changes
        # O'zgarishlarni kuzatish
        changes = {}

        # Update allowed fields
        # Ruxsat etilgan maydonlarni yangilash
        allowed_fields = [
            'end_of_service_benefit',
            'unused_leave_days',
            'pending_salary_days',
            'pending_bonus',
            'other_allowances',
            'advance_payments',
            'loan_balance',
            'other_deductions',
            'deduction_notes'
        ]

        for field, value in updated_fields.items():
            if field in allowed_fields:
                old_value = getattr(settlement, field)
                setattr(settlement, field, value)
                changes[field] = {
                    'old': float(old_value) if isinstance(old_value, Decimal) else old_value,
                    'new': float(value) if isinstance(value, Decimal) else value
                }

        # Add adjustment to calculation notes
        # Sozlashni hisoblash eslatmalariga qo'shish
        adjustment_note = f"\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] Adjusted by {adjusted_by.full_name}: {adjustment_reason}"
        settlement.calculation_notes = (settlement.calculation_notes or "") + adjustment_note

        # Totals will be recalculated on save
        # Jami saqlanishda qayta hisoblanadi
        settlement.save()

        # Log activity
        log_activity(
            user=adjusted_by,
            action="SETTLEMENT_ADJUSTED",
            model_name="TerminationSettlement",
            object_id=settlement.id,
            changes={
                "employee": settlement.employee.full_name,
                "adjustment_reason": adjustment_reason,
                "changes": changes,
                "new_net_amount": float(settlement.net_amount)
            }
        )

        return settlement