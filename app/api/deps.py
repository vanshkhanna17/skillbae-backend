# app/api/deps.py


from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED

from app.core.exceptions import AppException
from app.core.jwt import decode_token
from app.db.session import get_session
from app.models.user import User
from app.repo.comments_repo import CommentsRepo
from app.repo.feed_repo import FeedRepo
from app.repo.refresh_token_repo import RefreshTokenRepo
from app.repo.user_repo import UserRepo
from app.schemas.user import UserDetails
from app.services.auth_service import AuthService
from app.services.feed_service import FeedService
from app.services.user_service import UserService
from app.structures.tokens import AccessTokenPayload

oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl="/auth/login")


# repos
async def get_user_repo(
    session: AsyncSession = Depends(get_session),
) -> UserRepo:
    return UserRepo(session)


async def get_refresh_token_repo(
    session: AsyncSession = Depends(get_session),
) -> RefreshTokenRepo:
    return RefreshTokenRepo(session)


async def get_feed_repo(session: AsyncSession = Depends(get_session)) -> FeedRepo:
    return FeedRepo(session)


async def get_comments_repo(
    session: AsyncSession = Depends(get_session),
) -> CommentsRepo:
    return CommentsRepo(session)


# services
async def get_user_service(repo: UserRepo = Depends(get_user_repo)) -> UserService:
    return UserService(repo)


async def get_auth_service(
    repo: UserRepo = Depends(get_user_repo),
    refresh_repo: RefreshTokenRepo = Depends(get_refresh_token_repo),
) -> AuthService:
    return AuthService(repo, refresh_repo)


async def get_feeds_service(
    feed_repo: FeedRepo = Depends(get_feed_repo),
    comments_repo: CommentsRepo = Depends(get_comments_repo),
) -> FeedService:
    return FeedService(feed_repo, comments_repo)


# functions
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    # ↑ FastAPI automatically:
    #   - Reads the "Authorization: Bearer <token>" header
    #   - Extracts the token string
    #   - Passes it as the `token` argument here
    repo: UserRepo = Depends(get_user_repo),
) -> UserDetails:
    token_payload: AccessTokenPayload | None = decode_token(token)
    if token_payload is None:
        raise AppException(
            status_code=HTTP_401_UNAUTHORIZED,
            error="Unauthorized",
            message="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id: Optional[str] = token_payload["sub"] if token_payload["sub"] else None
    if user_id is None:
        raise AppException(
            status_code=HTTP_401_UNAUTHORIZED,
            error="Unauthorized",
            message="Token missing required user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user: User | None = await repo.get_by_id(int(user_id))
    if not user:
        raise AppException(
            status_code=HTTP_401_UNAUTHORIZED,
            error="Unauthorized",
            message="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UserDetails.model_validate(user)
