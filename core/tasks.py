from celery import shared_task
from core.backup_routine import executar_backups

@shared_task
def iniciar_backup_tarefa():
    executar_backups()

@shared_task
def tarefa_exemplo():
    print("Tarefa Celery executada com sucesso!")
    return "Tarefa concluída"
