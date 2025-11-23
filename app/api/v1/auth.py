from fastapi import APIRouter, Depends

from app.api.deps import get_auth_service
from app.schemas.user import Token, UserCreate, UserDetails, UserInDb, UserLogin
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserDetails)
async def register_user(
    data: UserCreate, auth_service: AuthService = Depends(get_auth_service)
) -> UserInDb:
    user = await auth_service.register(data)
    return user


@router.post("/login", response_model=Token)
async def login(
    creds: UserLogin, auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    token = await auth_service.login(creds.email, creds.password)
    return Token(access_token=token)
