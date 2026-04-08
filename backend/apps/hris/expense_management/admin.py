from django.contrib import admin
from .models import ExpenseClaim

@admin.register(ExpenseClaim)
class ExpenseClaimAdmin(admin.ModelAdmin):
    list_display = ('employee', 'title', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'title')
    date_hierarchy = 'created_at'
