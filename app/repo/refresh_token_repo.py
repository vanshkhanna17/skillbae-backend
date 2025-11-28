"""
RefreshToken repository — all DB operations for refresh token management.

Why a repository?
-------------------
To follow clean architecture:
 - Routes → call Services
 - Services → call Repositories
 - Repositories → talk to the database

This separation keeps your codebase scalable, testable, and modular.

This repo covers:
 - Creating new refresh-token DB rows
 - Looking up tokens by hash or by jti
 - Revoking a single token
 - Revoking ALL tokens of a user (if reuse attack detected)
 - Rotating a token (mark old one replaced_by_jti)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RefreshTokens


class RefreshTokenRepo:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_refresh_token(
        self,
        jti: str,
        token_hash: str,
        user_id: int,
        expires_at: datetime,
        meta: Optional[str] = None,
    ) -> RefreshTokens:
        refresh_token = RefreshTokens(
            jti=jti,
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            meta_data=meta,
        )
        self.session.add(refresh_token)
        await self.session.commit()
        await self.session.refresh(refresh_token)
        return refresh_token

    async def get_refresh_token_by_hash(
        self, token_hash: str
    ) -> Optional[RefreshTokens]:
        query = select(RefreshTokens).where(RefreshTokens.token_hash == token_hash)
        token = await self.session.execute(query)
        return token.scalar_one_or_none()

    async def get_refresh_token_by_jti(self, jti: str) -> Optional[RefreshTokens]:
        query = select(RefreshTokens).where(RefreshTokens.jti == jti)
        token = await self.session.execute(query)
        return token.scalar_one_or_none()

    async def revoke_refresh_token(self, token: RefreshTokens) -> None:
        token.is_revoked = True
        await self.session.commit()
        await self.session.refresh(token)

    async def revoke_all_refresh_tokens_for_user(self, user_id: int):
        query = select(RefreshTokens).where(
            RefreshTokens.user_id == user_id, RefreshTokens.is_revoked == False
        )
        result = await self.session.execute(query)
        tokens = result.scalars().all()

        for token in tokens:
            token.is_revoked = True

        await self.session.commit()

    async def rotate_refresh_token(
        self, old_token: RefreshTokens, new_jti: str
    ) -> None:
        old_token.is_revoked = True
        old_token.replaced_by_jti = new_jti
        await self.session.commit()
        await self.session.refresh(old_token)
