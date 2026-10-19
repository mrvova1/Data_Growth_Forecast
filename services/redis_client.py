import redis.asyncio as redis
from core.config import settings

redis_client: redis.Redis | None = None

async def init_redis():
    global redis_client
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )

async def close_redis():
    if redis_client:
        await redis_client.close()

def get_redis() -> redis.Redis:
    if redis_client is None:
        raise RuntimeError("Redis is not initialized")
    return redis_client
