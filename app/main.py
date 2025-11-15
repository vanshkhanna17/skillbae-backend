from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version
)

@app.get("/")
def root():
    return {"message": "Welcome to SkillBae API!"}

@app.get("/ping")
async def ping():
    return {"ping": "pong"}