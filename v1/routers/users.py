from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from v1.app import User, UserCRUD, schemas
from v1.app.schemas import UserSchema
from v1.dependencies import require_scopes

__tags__ = ["user"]
__prefix__ = "/users"

router = APIRouter()


@router.get("/")
async def get_users(
    _: Annotated[User, Depends(require_scopes("users:read"))],
) -> list[UserSchema]:
    return await UserCRUD.get_all()


@router.post("/")
async def create_user(
    payload: schemas.UserPayload,
) -> UserSchema:
    """
    Creating user in the database. Payload must contain **username**, **email** and **password**
    Note:
    """
    user, is_created = await UserCRUD.create(payload)

    if is_created:
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exist."
        )


@router.get("/me")
async def get_current_user_info(
    current_user: Annotated[User, Depends(require_scopes("users:me"))],
) -> UserSchema:
    """Get current user information"""
    return current_user
