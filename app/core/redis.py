from redis.asyncio import Redis

from app.core.config import settings

redis_client: Redis | None = None


async def get_redis_client() -> Redis:
    global redis_client

    if redis_client is None:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

    return redis_client


async def close_redis_client() -> None:
    global redis_client

    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None
