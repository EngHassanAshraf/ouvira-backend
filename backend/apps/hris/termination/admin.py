from django.contrib import admin
from .models import Termination

@admin.register(Termination)
class TerminationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'termination_date', 'last_working_day', 'is_voluntary')
    list_filter = ('is_voluntary', 'termination_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'reason')
    date_hierarchy = 'termination_date'
