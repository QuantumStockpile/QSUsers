from ms_core import AbstractModel
from tortoise import fields


class ExtendedAbstractModel(AbstractModel):
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:  # type: ignore
        abstract = True


class User(ExtendedAbstractModel):
    username = fields.TextField()
    email = fields.TextField()
    password_hash = fields.TextField()
    is_active = fields.BooleanField()

    role: fields.ForeignKeyRelation["Role"] = fields.ForeignKeyField(
        "models.Role", "users"
    )

    class Meta:  # type: ignore
        table = "users"


class Role(ExtendedAbstractModel):
    description = fields.CharField(24)

    users: fields.ReverseRelation[User]

    class Meta:  # type: ignore
        table = "roles"
