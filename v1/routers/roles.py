from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from v1.app import RoleCRUD, schemas

__tags__ = ["role"]
__prefix__ = "/roles"

from v1.dependencies import require_role

router = APIRouter()


@router.post("/")
async def create_role(
    payload: schemas.RolePayload, _: Annotated[Any, Depends(require_role("admin"))]
) -> schemas.RoleSchema:
    role, is_created = await RoleCRUD.create(payload)

    if is_created:
        return role
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Role already exist."
        )


@router.post("/elevate")
async def elevate_user(
    target_email: Annotated[str, Query(max_length=32)],
    _: Annotated[Any, Depends(require_role("admin"))],
) -> bool:
    return await RoleCRUD.elevate_role(target_email)


@router.get("/")
async def get_all(
    _: Annotated[Any, Depends(require_role("user"))],
) -> list[schemas.RoleSchema]:
    return await RoleCRUD.get_all()
