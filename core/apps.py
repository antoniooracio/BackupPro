from django.apps import AppConfig
from django.db.models.signals import post_migrate

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from core.backup_routine import iniciar_thread_agendamento
        iniciar_thread_agendamento()

