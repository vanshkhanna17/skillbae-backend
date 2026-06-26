import json

from app.core.event_bus import event_bus
from app.core.redis import get_redis_client


async def redis_subscriber():
    redis_client = await get_redis_client()
    pubsub = redis_client.pubsub()

    await pubsub.psubscribe(*event_bus.patterns())

    async for message in pubsub.listen():
        if message["type"] != "pmessage":
            continue
        data = json.loads(message["data"])
        await event_bus.dispatch(
            message["channel"], data["topic"], data.get("payload", {})
        )
