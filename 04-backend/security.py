"""Password hashing and access tokens, independent of HTTP."""

from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from config import settings

ALGORITHM = "HS256"
ISSUER = "course-catalog-api"
MAX_USER_ID = 2**63 - 1  # PostgreSQL bigint

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("not-a-real-password")


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(user_id),
        "iss": ISSUER,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(claims, settings.secret_key, algorithm=ALGORITHM)


def read_access_token(token: str) -> int:
    claims = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[ALGORITHM],
        issuer=ISSUER,
        options={"require": ["exp", "sub", "iss"]},
    )
    subject = claims["sub"]
    if not (isinstance(subject, str) and subject.isascii() and subject.isdecimal() and len(subject) <= 19):
        raise jwt.InvalidTokenError("sub is not a user id")
    user_id = int(subject)
    if not 1 <= user_id <= MAX_USER_ID:
        raise jwt.InvalidTokenError("sub is out of range")
    return user_id
