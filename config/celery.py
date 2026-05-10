import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')


def get_celery_app():
    from celery import Celery

    app = Celery('ams_backend')
    app.config_from_object('django.conf:settings', namespace='CELERY')
    app.autodiscover_tasks()
    return app
