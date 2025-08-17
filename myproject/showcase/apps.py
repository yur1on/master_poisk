from django.apps import AppConfig


class ShowcaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'showcase'

    def ready(self):
        import showcase.signals  # Импорт сигналов



