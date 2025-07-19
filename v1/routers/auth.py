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


async def _get_user_roles_and_scopes(user: User) -> tuple[list, list, list]:
    """
    Get user roles and aggregate scopes.
    Returns: (role_ids, role_names, aggregated_scopes)
    """
    user_roles = await user.roles.all()
    if not user_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no assigned roles",
        )

    all_user_scopes = set()
    role_names = []
    role_ids = []

    for role in user_roles:
        role_scopes = auth.get_scopes_for_role(role.name)
        all_user_scopes.update(role_scopes)
        role_names.append(role.name)
        role_ids.append(role.id)

    return role_ids, role_names, list(all_user_scopes)


def _create_token_data(user_email: str, role_ids: list, role_names: list) -> dict:
    """Create standardized token data payload."""
    return {
        "sub": user_email,
        "roles": role_ids,
        "role_names": role_names,
    }


def _set_auth_cookie(response: Response, access_token: str) -> None:
    """Set authentication cookie with standard parameters."""
    response.set_cookie(
        "Authorization",
        f"Bearer {access_token}",
        max_age=settings.security.access_token_expire_minutes * 60,
        httponly=True,
    )


def _decode_jwt_token(token: str, secret_key: str) -> dict:
    """Decode JWT token with error handling."""
    try:
        print(token, secret_key, settings.security.algorithm)
        return jwt.decode(
            token,
            secret_key,
            algorithms=[settings.security.algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def _validate_user_by_email(email: str) -> User:
    """Validate and return user by email."""
    user = await UserCRUD.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _filter_scopes(requested_scopes: list, available_scopes: list) -> list:
    """Filter requested scopes to only include allowed ones."""
    if not requested_scopes:
        return available_scopes
    return [scope for scope in requested_scopes if scope in available_scopes]


@router.post("/token")
async def login_for_token(
    *, form_data: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response
) -> schemas.TokenSchema:
    user = await _validate_user_by_email(form_data.username)

    if not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The password is incorrect"
        )

    role_ids, role_names, user_scopes = await _get_user_roles_and_scopes(user)
    final_scopes = _filter_scopes(form_data.scopes or [], user_scopes)

    token_data = _create_token_data(user.email, role_ids, role_names)
    access_token = auth.create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=settings.security.access_token_expire_minutes),
        scopes=final_scopes,
    )

    refresh_token = auth.create_refresh_token(
        email=user.email,
        expires_delta=timedelta(days=settings.security.refresh_token_expire_days),
    )

    _set_auth_cookie(response, access_token)

    return schemas.TokenSchema(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        scopes=final_scopes,
    )


@router.post("/introspect")
async def introspect_token(
    request: Request, token_data: schemas.TokenIntrospectionRequest
):
    try:
        payload = _decode_jwt_token(token_data.token, settings.security.secret_key)
        return {"active": True, "payload": payload, "scopes": payload.get("scopes", [])}
    except jwt.ExpiredSignatureError:
        return {"active": False, "error": "expired"}
    except jwt.InvalidTokenError:
        return {"active": False, "error": "invalid"}


@router.post("/refresh")
async def refresh_token(
    payload: schemas.RefreshTokenSchema, response: Response
) -> schemas.TokenSchema:
    refresh_payload = _decode_jwt_token(
        payload.refresh_token, settings.security.refresh_secret_key
    )

    if refresh_payload.get("token_type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid token type")

    email = refresh_payload.get("sub")
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = await _validate_user_by_email(email)
    role_ids, role_names, user_scopes = await _get_user_roles_and_scopes(user)

    token_data = _create_token_data(user.email, role_ids, role_names)
    access_token = auth.create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=settings.security.access_token_expire_minutes),
        scopes=user_scopes,
    )

    _set_auth_cookie(response, access_token)

    return schemas.TokenSchema(
        access_token=access_token,
        refresh_token=payload.refresh_token,
        token_type="bearer",
        scopes=user_scopes,
    )


@router.get("/logout")
async def logout(
    response: Response, _: Annotated[User, Security(get_current_active_user)]
):
    response.delete_cookie(key="Authorization")
    return {"message": "Logout successful"}


@router.get("/me/scopes")
async def get_my_scopes(
    current_user: Annotated[User, Security(get_current_active_user)],
) -> dict:
    """Get current user's available scopes from all assigned roles"""
    try:
        role_ids, role_names, all_scopes = await _get_user_roles_and_scopes(
            current_user
        )

        # Build detailed role info
        user_roles = await current_user.roles.all()
        role_info = [
            {
                "name": role.name,
                "id": role.id,
                "scopes": auth.get_scopes_for_role(role.name),
            }
            for role in user_roles
        ]

        return {
            "user": current_user.email,
            "roles": role_info,
            "available_scopes": all_scopes,
        }
    except HTTPException:
        return {
            "user": current_user.email,
            "roles": [],
            "available_scopes": [],
        }


@router.get("/me/roles")
async def get_my_roles(
    current_user: Annotated[User, Security(get_current_active_user)],
) -> dict:
    """Get current user's assigned roles with details"""
    user_roles = await current_user.roles.all()

    roles_data = [
        {
            "id": role.id,
            "name": role.name,
            "scopes": auth.get_scopes_for_role(role.name),
            "created_at": getattr(role, "created_at", None),
            "updated_at": getattr(role, "updated_at", None),
        }
        for role in user_roles
    ]

    return {
        "user": current_user.email,
        "roles": roles_data,
        "total_roles": len(roles_data),
    }


@router.post("/me/check-permission")
async def check_user_permission(
    permission_request: schemas.PermissionCheckRequest,
    current_user: Annotated[User, Security(get_current_active_user)],
) -> dict:
    """Check if current user has specific permission/scope"""
    try:
        _, _, all_scopes = await _get_user_roles_and_scopes(current_user)
        has_permission = permission_request.scope in all_scopes
    except HTTPException:
        all_scopes = []
        has_permission = False

    return {
        "user": current_user.email,
        "scope": permission_request.scope,
        "has_permission": has_permission,
        "user_scopes": all_scopes,
    }
