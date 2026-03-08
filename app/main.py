from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.feed import router as feed_router
from app.api.v1.users import router as user_router
from app.core.config import settings

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

app.include_router(auth_router, tags=["Auth"], prefix="/auth")
app.include_router(user_router, tags=["User"], prefix="/users")
app.include_router(feed_router, tags=["Feed"], prefix="/feed")


@app.get("/")
def root():
    return {"message": "Welcome to SkillBae API!"}


@app.get("/ping")
async def ping():
    return {"ping": "pong"}
