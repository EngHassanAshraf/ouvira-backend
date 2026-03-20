from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.hris.core'
    label = "hris_core"
    
    def ready(self):
        import apps.hris.core.signals