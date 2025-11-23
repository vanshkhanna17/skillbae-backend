import hashlib

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def create_hashed_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


def create_hashed_token(token: str) -> str:
    """
    Hash a refresh token using SHA-256 and return its hex digest.

    Why SHA-256?
    -------------
    - Fast, simple, widely supported
    - Non-reversible: raw token cannot be reconstructed
    - Produces a fixed-length 64-char hex string
    - Perfect for lookup because each refresh token is unique

    Why not bcrypt or argon2?
    --------------------------
    - bcrypt/argon2 are slow, intentionally — ideal for password hashing
    - Refresh tokens must be hashed and checked frequently and quickly
      during login/refresh flows
    - SHA-256 is perfectly acceptable here because:
         (a) refresh tokens are long, random, unguessable
         (b) hashing is purely to prevent storing them in plaintext
         (c) tokens have short validity and are rotated on every use

    Example:
        raw_token    = 'eyJhbGciOiJIUzI1NiIsInR5cC...'
        hashed_token = hash_token(raw_token)

    Returns
    -------
    str : hex-encoded SHA-256 hash
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
