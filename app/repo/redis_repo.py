from redis.asyncio.client import Redis


class RedisRepo:
    def __init__(self, redis_client: Redis) -> None:
        self.redis_client: Redis = redis_client

    async def publish_content(self, channel: str, content: str):
        return await self.redis_client.publish(channel, content)
