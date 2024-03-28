from celery import Celery
from celery.signals import worker_init
from dotenv import load_dotenv
import os

load_dotenv()
APP_ENV = os.getenv("APP_ENV")
if APP_ENV == "development":
    load_dotenv(dotenv_path=".env.development")
elif APP_ENV == "github":
    load_dotenv(dotenv_path=".env.github")
elif APP_ENV == "docker":
    load_dotenv(dotenv_path=".env.docker")
elif APP_ENV == "production":
    load_dotenv(dotenv_path=".env")

REDIS_BROKER = os.getenv("REDIS_BROKER")
REDIS_BACKEND = os.getenv("REDIS_BACKEND")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_HOST = str(os.getenv("REDIS_HOST"))

redbeat_redis_url = REDIS_BROKER

celeryapp = Celery(
    "celeryworker",
    broker=REDIS_BROKER,
    backend=REDIS_BACKEND,
    include=["routers.auth", "routers.dashboard", "routers.upload", "routers.content", "routers.settings", "routers.jobs", "routers.options", "routers.machines", "routers.billing", "utils"],
    broker_connection_retry=False,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    worker_prefetch_multiplier=1,
    task_ignore_result=True
)

def restore_all_unacknowledged_messages():
    conn = celeryapp.connection(transport_options={'visibility_timeout': 0})
    qos = conn.channel().qos
    qos.restore_visible()
    print('Unacknowledged messages restored')

@worker_init.connect
def configure(sender=None, conf=None, **kwargs):
    restore_all_unacknowledged_messages()

if __name__ == '__main__':
    celeryapp.start()