from pydantic import BaseModel, constr, EmailStr
from tortoise.contrib.pydantic import pydantic_model_creator

from .models import Role, User


class UserPayload(BaseModel):
    username: str
    email: EmailStr
    password: constr(min_length=8)


UserSchema = pydantic_model_creator(User)


class RolePayload(BaseModel):
    name: str


RoleSchema = pydantic_model_creator(Role)


class CredentialsRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8)


class TokenData(BaseModel):
    email: EmailStr
    scopes: list[str]


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    scopes: list[str] | None = None


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class TokenIntrospectionRequest(BaseModel):
    token: str


class PermissionCheckRequest(BaseModel):
    scope: str
