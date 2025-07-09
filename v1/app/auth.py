import datetime as dt
from datetime import datetime, timedelta

import jwt
from fastapi.security import (
    OAuth2PasswordBearer,
)
import bcrypt

from v1.settings import settings

SECRET_KEY, ALGORITHM = settings.security.secret_key, settings.security.algorithm

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "users:me": "Read information about the current user.",
        "users:read": "Read users.",
    },
)


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode("utf-8")


def verify_password(password: str, hash: str) -> bool:
    password_enc = password.encode("utf-8")
    hash_enc = hash.encode("utf-8")
    return bcrypt.checkpw(password_enc, hash_enc)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(dt.UTC) + (
        expires_delta if expires_delta else timedelta(minutes=60 * 60)
    )
    to_encode.update({"exp": expire, "token_type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(email: str, expires_delta: timedelta | None = None) -> str:
    to_encode: dict[str, str | datetime] = {"sub": email, "token_type": "refresh"}
    expire = datetime.now(dt.UTC) + (
        expires_delta
        if expires_delta
        else timedelta(days=settings.security.refresh_token_expire_days)
    )
    to_encode["exp"] = expire

    return jwt.encode(
        to_encode, settings.security.refresh_secret_key, algorithm=ALGORITHM
    )
