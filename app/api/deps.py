# app/api/deps.py


from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED

from app.core.jwt import decode_token
from app.db.session import get_session
from app.repo.user_repo import UserRepo
from app.schemas.user import UserDetails
from app.services.auth_service import AuthService
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_user_repo(
    session: AsyncSession = Depends(get_session),
):
    return UserRepo(session)


async def get_user_service(repo: UserRepo = Depends(get_user_repo)):
    return UserService(repo)


async def get_auth_service(repo: UserRepo = Depends(get_user_repo)):
    return AuthService(repo)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    # ↑ FastAPI automatically:
    #   - Reads the "Authorization: Bearer <token>" header
    #   - Extracts the token string
    #   - Passes it as the `token` argument here
    repo: UserRepo = Depends(get_user_repo),
) -> UserDetails:
    token_payload = decode_token(token)
    if token_payload is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id: Optional[str] = token_payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Token missing required user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await repo.get_user_by_id(int(user_id))
    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UserDetails.model_validate(user)
