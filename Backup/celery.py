from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Define o módulo de configuração do Django para o Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backup.settings')

app = Celery('Backup')

# Carrega as configurações do Django no Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobre automaticamente as tasks nos aplicativos instalados
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
