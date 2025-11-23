from typing import TypedDict


class Token(TypedDict):
    access_token: str
    refresh_token: str


class AccessTokenPayload(TypedDict):
    sub: str
    exp: str


class RefreshTokenPayload(AccessTokenPayload):
    jti: str
