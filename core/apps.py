from django.apps import AppConfig
from celery import shared_task

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'