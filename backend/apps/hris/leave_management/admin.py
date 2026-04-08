from django.contrib import admin
from .models import LeaveType, LeaveRequest

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'days_per_year')
    search_fields = ('name', 'code')

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'approved_by')
    list_filter = ('status', 'leave_type', 'start_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    date_hierarchy = 'start_date'
