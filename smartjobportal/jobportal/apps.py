from django.apps import AppConfig

class JobportalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobportal'
    verbose_name = 'SmartJobPortal'

    def ready(self):
        import jobportal.signals  # noqa
