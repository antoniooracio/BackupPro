from __future__ import absolute_import, unicode_literals

# Este código garante que o Celery seja carregado junto com o Django
from Backup.celery import app as celery_app

__all__ = ('celery_app',)
