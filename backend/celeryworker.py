from celery import Celery
from utils import REDIS_BROKER, REDIS_BACKEND

celeryapp = Celery(
    "celeryworker",
    broker=REDIS_BROKER,
    backend=REDIS_BACKEND,
    include=["routers.auth", "routers.dashboard", "routers.upload", "routers.content", "routers.settings", "routers.jobs", "routers.options", "routers.machines", "routers.billing"],
    broker_connection_retry=False,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10
)

if __name__ == '__main__':
    celeryapp.start()