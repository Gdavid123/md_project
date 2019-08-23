import os

from celery import Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

celery_apps = Celery('celery')

celery_apps.config_from_object('celery_tasks.config')

celery_apps.autodiscover_tasks(['celery_tasks.sms','celery_tasks.email'])