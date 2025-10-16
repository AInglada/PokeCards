import os
from celery import Celery
from celery.schedules import crontab

# Establish the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create a new Celery application instance
app = Celery('pokemon_tcg')

# Configurate Celery using the options in settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodetect tasks in tasks.py files of installed apps
app.autodiscover_tasks()

# Configuration of periodic tasks (schedule)
app.conf.beat_schedule = {
    'check-low-stock-every-morning': {
        'task': 'apps.products.tasks.check_low_stock_task',
        'schedule': crontab(hour=9, minute=0),
    },
    'process-abandoned-carts-every-6-hours': {
        'task': 'apps.orders.tasks.process_abandoned_carts_task',
        'schedule': crontab(hour='*/6', minute=0),
    },
    'cleanup-old-carts-daily': {
        'task': 'apps.orders.tasks.cleanup_old_carts_task',
        'schedule': crontab(hour=0, minute=0),
    },
}
