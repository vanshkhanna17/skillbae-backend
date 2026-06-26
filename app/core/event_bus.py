from typing import Awaitable, Callable

Handler = Callable[[str, dict], Awaitable[None]]


class RedisEventBus:
    def __init__(self) -> None:
        self.handlers: dict[str, dict[str, Handler]] = {}

    def register(self, namesapce: str, topic: str, handler: Handler):
        self.handlers.setdefault(namesapce, {})[topic] = handler

    def patterns(self):
        return [f"{ns}:*" for ns in self.handlers]

    async def dispatch(self, channel: str, topic: str, payload: dict):
        namespace = channel.split(":")[0]
        handler = self.handlers.get(namespace, {}).get(topic)
        if handler:
            await handler(channel, payload)


event_bus = RedisEventBus()
