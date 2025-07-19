from ms_core import AbstractModel
from tortoise import fields


class ExtendedAbstractModel(AbstractModel):
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:  # type: ignore
        abstract = True


class User(ExtendedAbstractModel):
    username = fields.TextField()
    email = fields.CharField(max_length=255, unique=True)
    password_hash = fields.TextField()
    is_active = fields.BooleanField()

    roles: fields.ManyToManyRelation["Role"] = fields.ManyToManyField(
        "models.Role", related_name="users", through="user_roles"
    )

    class Meta:  # type: ignore
        table = "users"


class Role(ExtendedAbstractModel):
    name = fields.CharField(24)

    users: fields.ManyToManyRelation[User]

    class Meta:  # type: ignore
        table = "roles"
