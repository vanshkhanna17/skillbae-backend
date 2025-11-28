"""
JWT creation & decoding utilities for SkillBae Auth System.

We intentionally separate ACCESS and REFRESH tokens:

ACCESS TOKEN:
 - Short-lived (e.g., 15 minutes)
 - Contains only 'sub' (user id) and 'exp'
 - Used for authenticating API requests
 - If stolen → limited impact because expires fast

REFRESH TOKEN:
 - Long-lived (e.g., 30 days)
 - Contains:
       - 'sub' (user id)
       - 'jti' (unique token ID, UUID4)
       - 'exp' (expiry)
 - Never accessible to JavaScript (stored only in HttpOnly cookie)
 - Rotated on every use to prevent replay attacks
 - Stored hashed in DB; jti stored for tracking

We also use TWO SEPARATE SECRETS:
  - SECRET_KEY → used for access tokens
  - REFRESH_SECRET_KEY → used for refresh tokens

This prevents an attacker who gains access to the access token secret
from minting refresh tokens (which would give full account takeover).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from jose import JWTError, jwt

from app.core.config import settings
from app.structures.tokens import AccessTokenPayload, RefreshTokenPayload


def create_jwt_token(user_id: str, expire_minutes: Optional[int] = None) -> str:
    if expire_minutes is None:
        expire_minutes = settings.access_token_expire_minutes

    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    exp_timestamp = int(expire.timestamp())

    payload = {"sub": user_id, "exp": exp_timestamp}

    encoded_jwt = jwt.encode(payload, settings.secret_key, settings.algorithm)

    return encoded_jwt


def create_refresh_token(
    user_id: str, expire_days: Optional[int] = None
) -> tuple[str, str, datetime]:
    if expire_days is None:
        expire_days = settings.refresh_token_expire_days
    expire = datetime.now(timezone.utc) + timedelta(days=expire_days)
    exp_timestamp = int(expire.timestamp())
    jti = str(uuid4())
    payload = {"sub": user_id, "jti": jti, "exp": exp_timestamp}
    refresh_token = jwt.encode(
        payload, settings.refresh_token_secret_key, settings.algorithm
    )
    expires_at_naive = expire.replace(tzinfo=None)
    return refresh_token, jti, expires_at_naive


def decode_token(token: str) -> Optional[AccessTokenPayload]:
    try:
        decoded_token = jwt.decode(token, settings.secret_key, settings.algorithm)
        return AccessTokenPayload(**decoded_token)
    except JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[RefreshTokenPayload]:
    try:
        decoded_token = jwt.decode(
            token, settings.refresh_token_secret_key, settings.algorithm
        )
        return RefreshTokenPayload(**decoded_token)
    except JWTError:
        return None
