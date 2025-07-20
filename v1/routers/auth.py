from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, Response, Depends, status
from fastapi.params import Security
from fastapi.security import OAuth2PasswordRequestForm
import jwt

from v1.app import UserCRUD, auth, schemas
from v1.app.models import User
from v1.dependencies import get_current_active_user
from v1.settings import settings

__tags__ = ["auth"]
__prefix__ = ""


router = APIRouter()


@router.post("/token")
async def login_for_token(
    *, form_data: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response
) -> schemas.TokenSchema:
    if not (user := await UserCRUD.get_by_email(form_data.username)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email could not be found",
        )

    if not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The password is incorrect"
        )

    access_token = auth.create_access_token(
        data={"sub": user.email, "role": (await user.role).id},
        expires_delta=timedelta(minutes=settings.security.access_token_expire_minutes),
    )

    refresh_token = auth.create_refresh_token(
        email=user.email,
        expires_delta=timedelta(days=settings.security.refresh_token_expire_days),
    )

    response.set_cookie(
        "Authorization",
        f"Bearer {access_token}",
        max_age=settings.security.access_token_expire_minutes * 60,
        httponly=True,
    )

    return schemas.TokenSchema(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/introspect")
async def introspect_token(
    request: Request, token_data: schemas.TokenIntrospectionRequest
):
    try:
        payload = jwt.decode(
            token_data.token,
            settings.security.secret_key,
            algorithms=[settings.security.algorithm],
        )
        return {"active": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"active": False, "error": "expired"}
    except jwt.InvalidTokenError:
        return {"active": False, "error": "invalid"}


@router.post("/refresh")
async def refresh_token(
    payload: schemas.RefreshTokenSchema, response: Response
) -> schemas.TokenSchema:
    try:
        refresh_payload = jwt.decode(
            payload.refresh_token,
            settings.security.refresh_secret_key,
            algorithms=[settings.security.algorithm],
        )
        if refresh_payload.get("token_type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")

        email = refresh_payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")

        user = await UserCRUD.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        access_token = auth.create_access_token(
            data={"sub": user.email, "role": (await user.role).id},
            expires_delta=timedelta(
                minutes=settings.security.access_token_expire_minutes
            ),
        )

        response.set_cookie(
            "Authorization",
            f"Bearer {access_token}",
            max_age=settings.security.access_token_expire_minutes * 60,
            httponly=True,
        )

        return schemas.TokenSchema(
            access_token=access_token,
            refresh_token=payload.refresh_token,
            token_type="bearer",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.get("/logout")
async def logout(
    response: Response, _: Annotated[User, Security(get_current_active_user)]
):
    response.delete_cookie(key="Authorization")

    return {"message": "Logout successful"}
