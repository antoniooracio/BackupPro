from django.apps import AppConfig
import threading
from django.db.models.signals import post_migrate

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Garantir que o agendamento seja iniciado apenas uma vez
        global agendamento_iniciado
        if not getattr(self, '_agendamento_iniciado', False):
            self._agendamento_iniciado = True  # Marca como iniciado
            from core.backup_routine import iniciar_thread_agendamento
            iniciar_thread_agendamento()


