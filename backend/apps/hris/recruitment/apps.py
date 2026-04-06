from django.apps import AppConfig


class RecruitmentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.hris.recruitment'
    label = 'hris_recruitment'

    def ready(self):
        # Register Domain Event Handlers for loose coupling
        from .application.handlers import register_recruitment_handlers
        register_recruitment_handlers()
