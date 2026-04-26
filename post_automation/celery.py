import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'post_automation.settings')

app = Celery('insta_automation')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
