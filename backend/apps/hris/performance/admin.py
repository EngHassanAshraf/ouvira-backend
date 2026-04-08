from django.contrib import admin
from .models import KPI, EmployeeReview

@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_value')
    search_fields = ('title',)

@admin.register(EmployeeReview)
class EmployeeReviewAdmin(admin.ModelAdmin):
    list_display = ('employee', 'reviewer', 'review_date', 'score')
    list_filter = ('review_date', 'score')
    search_fields = ('employee__first_name', 'employee__last_name', 'reviewer__first_name')
    date_hierarchy = 'review_date'
