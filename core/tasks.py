from celery import shared_task

@shared_task
def tarefa_exemplo():
    print("Tarefa Celery executada com sucesso!")
    return "Tarefa concluída"
