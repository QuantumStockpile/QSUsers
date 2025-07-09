from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.params import Security
from fastapi.security import OAuth2PasswordBearer
import jwt

from v1.app.auth import oauth2_scheme
from v1.settings import settings
from v1.app import UserCRUD, User


class OAuth2PasswordBearerCookies(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> str | None:
        exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if not (authorization := request.headers.get("Authorization")):
            if not (authorization := request.cookies.get("Authorization")):
                raise exc

        scheme, _, token = authorization.partition(" ")

        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise exc
            else:
                return None
        return token


SECRET_KEY, ALGORITHM = settings.security.secret_key, settings.security.algorithm


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("token_type") != "access":
            raise credentials_exception

        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    if not (user := await UserCRUD.get_by_email(email)):
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Security(get_current_user, scopes=["users:me"])],
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user."
        )

    return current_user


def require_role(required_role_desc: str):
    async def role_checker(user: User = Depends(get_current_active_user)):
        if (await user.role).description != required_role_desc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return role_checker
