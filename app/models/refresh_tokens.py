"""
RefreshToken ORM model for SkillBae.

Purpose:
    - Represent refresh tokens in the database for rotation, revocation
    and reuse-detection.
    - Store only safe data: a unhashed identifier (jti) for quick lookup,
    and a hash of the raw refresh token (token_hash) not the raw token itself.
    - Track expiry, revocation status, replacement chain and optional meta
    (user-agent / IP) for auditing and anomaly detection.

Security rules implemented here:
    - NEVER store raw refresh token string in DB -> store SHA-256 hex digest only
    - Unique jti inside JWT payload to correlate JWT <-> DB row quickly
    - Mark tokens revoked rather than deleting (audit trail)
DB table: refresh_tokens

Fields:
    - id: internal primary key
    - jti: JWT ID embedded inside refresh JWT (UUID string)
    - token_hash: SHA-256 hex digest of the refresh token (unique)
    - user_id: FK to users.id (owner of the token)
    - created_at: when token row created
    - expires_at: when the token becomes invalid (UTC)
    - is_revoked: boolean flag to block a token without deleting the row
    - replaced_by_jti: if this token was rotated, points to the new token's jti
    - meta: optional free-text (user-agent + ip) for auditing
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class RefreshTokens(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, nullable=False
    )
    jti: Mapped[str] = mapped_column(
        String(36), index=True, nullable=False, unique=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    replaced_by_jti: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )
    meta_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
