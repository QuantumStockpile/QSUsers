import datetime as dt
from datetime import timedelta, datetime
from pprint import pprint
from typing import Union

import jwt
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from passlib.context import CryptContext

from v1.settings import settings

SECRET_KEY, ALGORITHM = settings.security.secret_key,\
                        settings.security.algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "users:me": "Read information about the current user.",
        "users:read": "Read users."
    },
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(dt.UTC) + (expires_delta if expires_delta else timedelta(minutes=60*60))
    to_encode["exp"] = expire

    return jwt.encode(to_encode, SECRET_KEY)
