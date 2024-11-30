from pydantic import BaseModel, constr, EmailStr
from tortoise.contrib.pydantic import pydantic_model_creator

from .models import User


class UserPayload(BaseModel):
    username: str
    email: EmailStr
    password: constr(min_length=8)


class CredentialsRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8)


UserSchema = pydantic_model_creator(User)


class TokenData(BaseModel):
    email: EmailStr
    scopes: list[str]


class TokenSchema(BaseModel):
    access_token: str
    token_type: str
