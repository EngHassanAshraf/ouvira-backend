from django.contrib import admin
from .models.base import Location
from .models.employee import Employee

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    # Admin panelda ko'rinadigan ustunlar
    list_display = ('id', 'name', 'city', 'country', 'is_active')

    # Qidiruv maydonlari
    search_fields = ('name', 'city', 'address')

    # Filtrlash (o'ng tomonda chiqadi)
    list_filter = ('country', 'is_active')

    # Tahrirlash sahifasida maydonlar ketma-ketligi
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'is_active')
        }),
        ('Manzil ma\'lumotlari', {
            'fields': ('address', 'city', 'country')
        }),
    )

    def save_model(self, request, obj, form, change):
        # Obyektni o'zini emas, ID-sini beramiz
        if hasattr(request, 'tenant') and not obj.company_id:
            # request.tenant.id — bu o'sha bizga kerakli raqam
            obj.company_id = request.tenant.id

        super().save_model(request, obj, form, change)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'company', 'location', 'national_id')
    search_fields = ('employee_id', 'first_name', 'last_name', 'national_id')
    list_filter = ('company', 'location', 'gender')

    # Saudiya talablari bo'lgani uchun IQAMA (national_id) ni alohida guruhlab ko'rsatsa ham bo'ladi
    fieldsets = (
        ('Personal Info', {
            'fields': ('user', 'company', 'location', 'first_name', 'last_name', 'employee_id')
        }),
        ('Identification (KSA)', {
            'fields': ('national_id', 'passport_number', 'nationality')
        }),
        ('Additional Info', {
            'fields': ('date_of_birth', 'gender', 'marital_status', 'contact_number', 'personal_email')
        }),
    )