import os
from celery import Celery
from kombu import Exchange, Queue

app = Celery('notify_service')

app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@localhost:5672//'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

email_exchange = Exchange('email_exchange', type='direct', durable=True)

app.conf.task_queues = (
    Queue(
        'email_queue',
        exchange=email_exchange,
        routing_key='send_email',
        durable=True,
    ),
)

app.conf.task_default_queue = 'email_queue'
app.conf.task_default_exchange = 'email_exchange'
app.conf.task_default_routing_key = 'send_email'

# Auto-discover tasks from app modules
app.autodiscover_tasks(['app.tasks'], force=True)


app.conf.task_routes = {
    'app.tasks.email.send_email': {
        'queue': 'email_queue',
        'routing_key': 'send_email',
    }
}