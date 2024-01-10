# celery_config.py

from kombu import Exchange, Queue

CELERY_BROKER_URL = 'redis://127.0.0.1:8000/tasks'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:8000/tasks'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = 'UTC'
CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = (
    Queue('default', Exchange('default'), routing_key='default'),
)
