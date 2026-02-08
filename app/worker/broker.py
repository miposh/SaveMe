from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

from app.config.config import settings


def _build_redis_url() -> str:
    host = settings.redis_host
    port = settings.redis_port
    db = settings.get("redis_database", 0)
    password = settings.get("redis_password", "")
    if password:
        return f"redis://:{password}@{host}:{port}/{db}"
    return f"redis://{host}:{port}/{db}"


redis_url = _build_redis_url()

result_backend = RedisAsyncResultBackend(redis_url=redis_url)

broker = ListQueueBroker(url=redis_url).with_result_backend(result_backend)
