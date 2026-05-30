from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

from app.core.connection_manager import ws_connection_manger
from app.core.deps import get_redis
from app.core.jwt import decode_token
from app.structures.tokens import AccessTokenPayload

router: APIRouter = APIRouter()


async def get_token_from_ws(
    ws: WebSocket, token: str | None = Query(default=None)
) -> str | None:
    """
    Try cookie first (production path — browser sends HttpOnly cookie automatically).
    Fall back to query param (test path — TestClient can't forward cookies to WS).

    WHY keep both?
    Starlette's TestClient cookie jar doesn't forward to WS upgrade requests.
    Rather than fighting the test tooling, we accept a query param fallback.
    In production, the frontend never uses the query param — the cookie is always
    present.
    """
    cookie_token = ws.cookies.get("access_token")
    return cookie_token or token


@router.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    redis: Redis = Depends(get_redis),
    token: str | None = Depends(get_token_from_ws),
):

    if not token:
        await ws.accept()
        await ws.close(code=4001)
        return

    payload: AccessTokenPayload | None = decode_token(token)

    if payload is None:
        await ws.accept()
        await ws.close(code=4001)
        return

    user_id = payload["sub"]
    await ws.accept()

    ws_connection_manger.connect(int(user_id), ws)
    await redis.set(f"presence:{user_id}", "1", ex=86400)
    await ws.send_json({"topic": "connected", "payload": {"user_id": user_id}})

    try:
        while True:
            data = await ws.receive_json()
            await ws.send_json(data)
    except WebSocketDisconnect:
        was_last_connection: bool = ws_connection_manger.disconnect(int(user_id), ws)
        if was_last_connection:
            await redis.delete(f"presence:{user_id}")
