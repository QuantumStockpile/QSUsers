import enum

from ms_core import AbstractModel
from tortoise import fields


class UserType(enum.StrEnum):
    DEFAULT = enum.auto()
    ADMIN = enum.auto()


class User(AbstractModel):
    username = fields.TextField()
    email = fields.TextField()
    password_hash = fields.TextField()
    is_active = fields.BooleanField()
    type = fields.CharEnumField(UserType, default=UserType.DEFAULT)

    class Meta:  # type: ignore
        table = "users"
