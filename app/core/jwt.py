from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from app.core.config import settings


def create_jwt_token(user_id: str, expire_minutes: Optional[int] = None) -> str:
    if expire_minutes is None:
        expire_minutes = settings.access_token_expire_minutes

    expire = datetime.now() + timedelta(minutes=expire_minutes)

    payload = {"sub": user_id, "exp": expire}

    encoded_jwt = jwt.encode(payload, settings.secret_key, settings.algorithm)

    return encoded_jwt


def decode_token(token: str):
    try:
        decoded_token = jwt.decode(token, settings.secret_key, settings.algorithm)
        return decoded_token
    except JWTError:
        # Any error: invalid token, expired token, wrong signature, etc.
        return None
