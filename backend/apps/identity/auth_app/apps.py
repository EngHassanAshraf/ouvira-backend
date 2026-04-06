from django.apps import AppConfig


class AuthModuleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.identity.auth_app"

    def ready(self):
        import apps.identity.auth_app.receivers
