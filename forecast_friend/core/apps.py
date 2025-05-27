

from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'  # или как у тебя называется приложение

    def ready(self):
        import core.signals  # импортируем сигналы здесь
