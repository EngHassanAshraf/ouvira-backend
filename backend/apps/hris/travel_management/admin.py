from django.contrib import admin
from .models import TravelRequest

@admin.register(TravelRequest)
class TravelRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'destination', 'start_date', 'end_date', 'estimated_cost')
    list_filter = ('start_date', 'destination')
    search_fields = ('employee__first_name', 'employee__last_name', 'destination', 'purpose')
    date_hierarchy = 'start_date'
