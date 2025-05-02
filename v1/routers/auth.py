from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Response, Depends, status
from fastapi.params import Security
from fastapi.security import OAuth2PasswordRequestForm

from v1.app import UserCRUD, auth, schemas
from v1.app.models import UserType, User
from v1.dependencies import get_current_active_user
from v1.settings import settings

__tags__ = ["auth"]
__prefix__ = ""
user_type_to_scopes = {
    UserType.DEFAULT: {
        "users:me",
    },
    UserType.ADMIN: {
        "users:me",
        "users:read",
    },
}

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

    scopes = form_data.scopes if form_data.scopes else ["users:me"]
    allowed_scopes = user_type_to_scopes[user.type]
    print(allowed_scopes)
    print(user.type)
    print(UserType.ADMIN)
    if not set(form_data.scopes).issubset(allowed_scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Not enough permissions",
                "allowed_scopes": " ".join(allowed_scopes),
            },
            headers={"WWW-Authenticate": f"bearer"},
        )

    access_token_expires = timedelta(
        minutes=settings.security.access_token_expire_minutes
    )
    token = auth.create_access_token(
        data={"sub": user.email, "scopes": scopes}, expires_delta=access_token_expires
    )
    response.set_cookie(
        "Authorization",
        f"Bearer {token}",
        expires=settings.security.access_token_expire_minutes,
        httponly=True,
    )

    return schemas.TokenSchema(access_token=token, token_type="bearer")


@router.get("/logout")
async def logout(
    response: Response, _: Annotated[User, Security(get_current_active_user)]
):
    response.delete_cookie(key="Authorization")

    return {"message": "Logout successful"}
