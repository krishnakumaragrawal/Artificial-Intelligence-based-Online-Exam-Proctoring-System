from datetime import timedelta
from typing import Any, Dict

import jwt
from passlib.context import CryptContext

from proctoring_platform.core.config import Settings
from proctoring_platform.core.time import now_utc


password_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return password_context.verify(plain_password, password_hash)


def create_access_token(user_id: int, settings: Settings) -> str:
    expires_at = now_utc() + timedelta(minutes=settings.access_token_minutes)
    payload: Dict[str, Any] = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> int:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return int(payload["sub"])
