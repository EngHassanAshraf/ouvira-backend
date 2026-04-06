from django.apps import AppConfig


class HrisCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.hris.hris_core'
    label = "hris_core"
    
    def ready(self):
        import apps.hris.hris_core.signals
