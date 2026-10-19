import os

from celery import Celery
from celery.signals import setup_logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('codelearn')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@setup_logging.connect
def configure_celery_logging(**kwargs):
    from django.conf import settings
    import logging.config

    logging.config.dictConfig(settings.LOGGING)
