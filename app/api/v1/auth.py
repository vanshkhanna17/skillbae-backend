from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import get_auth_service
from app.core.config import settings
from app.schemas.user import UserCreate, UserDetails, UserInDb, UserLogin
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserDetails)
async def register_user(
    data: UserCreate, auth_service: AuthService = Depends(get_auth_service)
) -> UserInDb:
    user = await auth_service.register(data)
    return user


@router.post("/login", response_model=dict[str, str])
async def login(
    creds: UserLogin,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    tokens = await auth_service.login(creds.email, creds.password)
    response.set_cookie(
        key="auth_refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite.value,
        path=settings.cookie_path,
        max_age=60 * 60 * 24 * settings.refresh_token_expire_days,
    )
    return {"access_token": tokens["access_token"], "token_type": "bearer"}


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    refresh_token: str = request.cookies.get("auth_refresh_token")
    new_tokens = await auth_service.rotate_refresh_token(refresh_token)
    response.set_cookie(
        key="auth_refresh_token",
        value=new_tokens["refresh_token"],
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite.value,
        path=settings.cookie_path,
        max_age=60 * 60 * 24 * settings.refresh_token_expire_days,
    )
    return {"access_token": new_tokens["access_token"], "token_type": "bearer"}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    refresh_token = request.cookies.get("auth_refresh_token")
    await auth_service.logout(refresh_token)
    response.delete_cookie(key="auth_refresh_token", path=settings.cookie_path)
    return {"logout": True, "message": "logout successful"}
