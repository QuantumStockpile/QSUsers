from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Security

from v1.app import schemas, UserCRUD, User

__tags__ = ["user"]
__prefix__ = "/users"

from v1.app.schemas import UserSchema

from v1.dependencies import get_current_user

router = APIRouter()


@router.get("/")
async def get_users(
    _: Annotated[User, Security(get_current_user, scopes=["users:read"])],
) -> list[UserSchema]:
    return await UserCRUD.get_all()


@router.post("/")
async def create_user(payload: schemas.UserPayload) -> UserSchema:
    """
    Creating user in the database. Payload must contain **username**, **email** and **password**

    :param payload: Payload for user.
    :return: None
    """
    user, is_created = await UserCRUD.create(payload)

    if is_created:
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exist."
        )
