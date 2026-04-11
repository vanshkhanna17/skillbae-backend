"""
AuthService: Business logic for SkillBae authentication.

Responsibility:
---------------
This class handles the execution of authentication rules such as:
 - Verifying user credentials during login
 - Creating access and refresh tokens
 - Storing refresh token metadata securely in DB
 - Rotating refresh tokens to prevent replay attacks
 - Detecting and responding to token reuse (security-critical)
 - Handling logout by revoking tokens

It does NOT:
-----------
 - Know anything about HTTP (no Response objects)
 - Set cookies
 - Manage database sessions outside repos
"""

from typing import Optional

from fastapi import status

from app.core.exceptions import AppException
from app.core.jwt import create_jwt_token, create_refresh_token, decode_refresh_token
from app.core.security import (
    create_hashed_password,
    create_hashed_token,
    verify_password,
)
from app.models.user import User, utc_now
from app.repo.refresh_token_repo import RefreshTokenRepo
from app.repo.user_repo import UserRepo
from app.schemas.user import UserCreate, UserInDb
from app.structures.tokens import Token


class AuthService:

    def __init__(self, user_repo: UserRepo, refresh_repo: RefreshTokenRepo) -> None:
        self.user_repo: UserRepo = user_repo
        self.refresh_repo: RefreshTokenRepo = refresh_repo

    async def register(self, data: UserCreate) -> UserInDb:
        existing_user: User | None = await self.user_repo.get_user_by_email(data.email)
        if existing_user:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message="User already exists",
                field="email",
            )
        hashed_password: str = create_hashed_password(data.password)
        user: User = await self.user_repo.create(data, hashed_password=hashed_password)
        return UserInDb.model_validate(user)

    async def login(
        self, email: str, password: str, meta: Optional[str] = None
    ) -> Token:
        user = await self.user_repo.get_user_by_email(email)
        if not user:
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error="Unauthorized",
                message="Invalid email",
                field="email",
            )

        if not verify_password(password, user.hashed_password):
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error="Unauthorized",
                message="Invalid password",
                field="password",
            )
        jwt_token = create_jwt_token(user_id=str(user.id))
        (refresh_token, jti, expires_at) = create_refresh_token(user_id=str(user.id))
        token_hash = create_hashed_token(refresh_token)
        await self.refresh_repo.create_refresh_token(
            jti, token_hash, user.id, expires_at
        )
        response_payload = {
            "access_token": jwt_token,
            "refresh_token": refresh_token,
        }
        return Token(**response_payload)

    async def logout(self, refresh_token: Optional[str]):
        """
        Logout user by revoking their refresh token.

        Notes:
        - If cookie missing → logout is still successful (idempotent)
        - Only revokes the specific refresh token used by this device/session
        """
        if not refresh_token:
            return
        token_hash = create_hashed_token(refresh_token)
        db_token = await self.refresh_repo.get_refresh_token_by_hash(token_hash)
        if db_token:
            await self.refresh_repo.revoke_refresh_token(db_token)

    async def rotate_refresh_token(self, refresh_token: str) -> Token:
        """
        Rotate refresh token securely.

        Steps performed:
        1. Ensure token exists in cookie (otherwise client is unauthenticated)
        2. Decode the token (to extract `sub` + `jti`)
        3. Hash token value and check if it exists in DB
        4. If NOT in DB but DO decodes → REPLAY ATTACK → revoke all user refresh tokens
        5. If found but revoked/expired → treat as replay, revoke all, deny
        6. If valid:
               - generate new refresh token
               - store it in DB
               - mark OLD token as revoked and linked to new token (audit trail)
               - issue fresh access token
        """
        if not refresh_token:
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error="Unauthorized",
                message="Missing refresh token",
            )

        decoded_token = decode_refresh_token(refresh_token)

        token_hash = create_hashed_token(refresh_token)

        old_refresh_token = await self.refresh_repo.get_refresh_token_by_hash(
            token_hash
        )

        if not old_refresh_token:
            if decoded_token and decoded_token["sub"]:
                await self.refresh_repo.revoke_all_refresh_tokens_for_user(
                    int(decoded_token["sub"])
                )
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error="Unauthorized",
                message="Invalid refresh token",
            )

        if old_refresh_token.is_revoked or old_refresh_token.expires_at < utc_now():
            sub = decoded_token.get("sub") if decoded_token else None
            if sub is not None:
                await self.refresh_repo.revoke_all_refresh_tokens_for_user(int(sub))
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error="Unauthorized",
                message="Refresh token expired",
            )

        new_refresh_token, new_jti, expires_at = create_refresh_token(
            str(old_refresh_token.user_id)
        )
        token_hash = create_hashed_token(new_refresh_token)
        await self.refresh_repo.create_refresh_token(
            new_jti, token_hash, old_refresh_token.user_id, expires_at
        )
        await self.refresh_repo.rotate_refresh_token(old_refresh_token, new_jti)
        new_access_token = create_jwt_token(str(old_refresh_token.user_id))
        response_payload = {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
        }
        return Token(**response_payload)
