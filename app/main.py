import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app.api.v1.auth import router as auth_router
from app.api.v1.feed import router as feed_router
from app.api.v1.users import router as user_router
from app.core.config import settings
from app.core.limiter import limiter

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s:    %(asctime)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
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


@app.get("/")
def root():
    logger.debug("Logging items")
    return {"message": "Welcome to SkillBae API!"}


@app.get("/ping")
async def ping():
    logger.debug("Logging ping in debug")
    return {"success": True}
