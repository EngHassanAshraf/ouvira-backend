from django.contrib import admin
from .models import LoginActivity, PasswordHistory, OTPRecord, PasswordResetToken


# @admin.register(OTPVerification)
# class OTPAdmin(admin.ModelAdmin):
#     list_display = (
#         "phone_number",
#         "otp_code",
#         "expires_at",
#         "attempts",
#         "is_blocked",
#         "blocked_until",
#         "created_at",
#     )
#     list_filter = ("is_blocked",)
#     search_fields = ("phone_number", "otp_code")
#     readonly_fields = ("created_at",)

admin.site.register(OTPRecord)
admin.site.register(LoginActivity)
admin.site.register(PasswordHistory)
admin.site.register(PasswordResetToken)
