from django.apps import AppConfig


class InternalAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.hris.internal_auth"
    label = "internal_auth"
    verbose_name = "Internal Auth"
