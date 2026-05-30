import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app.api.v1.auth import router as auth_router
from app.api.v1.feed import router as feed_router
from app.api.v1.users import router as user_router
from app.api.v1.ws import router as ws_router
from app.core.config import settings
from app.core.limiter import limiter
from app.core.redis import get_redis_client

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s:    %(asctime)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def redis_lifespan(app: FastAPI):
    redis: Redis = await get_redis_client()
    await redis.ping()  # pyright: ignore[reportGeneralTypeIssues]
    yield

    await redis.close()


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=redis_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def add_cache_control(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    response = await call_next(request)
    # default to no-store for all API responses
    if "Cache-Control" not in response.headers:
        response.headers["Cache-Control"] = "no-store"
    return response


app.include_router(auth_router, tags=["Auth"], prefix="/auth")
app.include_router(user_router, tags=["User"], prefix="/users")
app.include_router(feed_router, tags=["Feed"], prefix="/feed")
app.include_router(ws_router, tags=["WebSocket"], prefix="/websocket")


@app.get("/")
def root():
    logger.debug("Logging items")
    return {"message": "Welcome to SkillBae API!"}


@app.get("/ping")
async def ping():
    logger.debug("Logging ping in debug")
    return {"success": True}


@app.get("/redis-health")
async def redis_healthcheck():
    checks = {}
    try:
        redis = await get_redis_client()
        await redis.ping()  # pyright: ignore[reportGeneralTypeIssues]
        checks["redis"] = "up"
    except Exception as e:
        logger.error(f"Redis healthcheck failed: {e}")
        checks["redis"] = "down"

    overall = all(status == "up" for status in checks.values())

    return JSONResponse(
        status_code=200 if overall else 503,
        content=checks,
    )
