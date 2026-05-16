"""
Settlement Serializers / Hisob-kitob Serializerlari

Serializers for termination settlements
Tugatish hisob-kitoblari uchun serializerlar
"""

from rest_framework import serializers
from decimal import Decimal
from apps.hris.termination.models import TerminationSettlement, TerminationRequest


class TerminationSettlementListSerializer(serializers.ModelSerializer):
    """
    List serializer for settlements
    Hisob-kitoblar ro'yxati serializeri
    """
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_ready_for_payment = serializers.BooleanField(read_only=True)

    class Meta:
        model = TerminationSettlement
        fields = [
            'id',
            'employee',
            'employee_name',
            'termination_request',
            'status',
            'status_display',
            'gross_amount',
            'total_deductions',
            'net_amount',
            'payment_date',
            'is_ready_for_payment',
            'created_at'
        ]


class TerminationSettlementDetailSerializer(serializers.ModelSerializer):
    """
    Detail serializer for settlements
    Hisob-kitoblar tafsilot serializeri
    """
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_position = serializers.CharField(source='employee.position.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True, allow_null=True)

    calculated_by_name = serializers.CharField(source='calculated_by.full_name', read_only=True, allow_null=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True, allow_null=True)
    paid_by_name = serializers.CharField(source='paid_by.full_name', read_only=True, allow_null=True)

    is_ready_for_payment = serializers.BooleanField(read_only=True)
    payment_deadline = serializers.DateField(read_only=True, allow_null=True)

    class Meta:
        model = TerminationSettlement
        fields = [
            'id',
            # Employee & Termination
            'employee',
            'employee_name',
            'employee_position',
            'termination_request',
            'status',
            'status_display',
            # Settlement components
            'years_of_service',
            'end_of_service_benefit',
            'unused_leave_days',
            'unused_leave_amount',
            'pending_salary_days',
            'pending_salary_amount',
            'pending_bonus',
            'other_allowances',
            # Deductions
            'advance_payments',
            'loan_balance',
            'other_deductions',
            'deduction_notes',
            # Totals
            'gross_amount',
            'total_deductions',
            'net_amount',
            # Calculation
            'calculated_by',
            'calculated_by_name',
            'calculated_date',
            'calculation_notes',
            # Approval
            'approved_by',
            'approved_by_name',
            'approved_date',
            # Payment
            'payment_date',
            'payment_method',
            'payment_method_display',
            'payment_reference',
            'paid_by',
            'paid_by_name',
            # Deceased heir
            'paid_to_heir',
            'heir_relationship',
            'heir_identification',
            # Properties
            'is_ready_for_payment',
            'payment_deadline',
            # Attachments
            'attachment',
            # Timestamps
            'created_at',
            'updated_at'
        ]


class SettlementCreateSerializer(serializers.Serializer):
    """
    Serializer for creating settlement
    Hisob-kitob yaratish serializeri
    """
    termination_request = serializers.PrimaryKeyRelatedField(
        queryset=TerminationRequest.objects.filter(is_deleted=False)
    )
    years_of_service = serializers.DecimalField(
        required=True,
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.01")
    )
    unused_leave_days = serializers.DecimalField(
        required=True,
        max_digits=6,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    pending_salary_days = serializers.DecimalField(
        required=True,
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    end_of_service_benefit = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    pending_bonus = serializers.DecimalField(
        default=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    other_allowances = serializers.DecimalField(
        default=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    advance_payments = serializers.DecimalField(
        default=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    loan_balance = serializers.DecimalField(
        default=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    other_deductions = serializers.DecimalField(
        default=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    deduction_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000
    )
    calculation_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000
    )


class SettlementAdjustSerializer(serializers.Serializer):
    """
    Serializer for adjusting settlement
    Hisob-kitobni sozlash serializeri
    """
    adjustment_reason = serializers.CharField(required=True, max_length=1000)
    end_of_service_benefit = serializers.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    unused_leave_days = serializers.DecimalField(
        required=False,
        max_digits=6,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    pending_salary_days = serializers.DecimalField(
        required=False,
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    pending_bonus = serializers.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    other_allowances = serializers.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    advance_payments = serializers.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    loan_balance = serializers.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    other_deductions = serializers.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00")
    )
    deduction_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000
    )


class SettlementPaymentSerializer(serializers.Serializer):
    """
    Serializer for processing settlement payment
    Hisob-kitob to'lovini qayta ishlash serializeri
    """
    payment_date = serializers.DateField(required=True)
    payment_method = serializers.ChoiceField(
        choices=[
            ('bank_transfer', 'Bank Transfer'),
            ('check', 'Check'),
            ('cash', 'Cash')
        ]
    )
    payment_reference = serializers.CharField(required=True, max_length=100)
    paid_to_heir = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200
    )
    heir_relationship = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=50
    )
    heir_identification = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100
    )