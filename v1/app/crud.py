from . import schemas, models, auth


class UserCRUD:
    user = models.User

    @classmethod
    async def get_all(cls):
        return await cls.user.all()

    @classmethod
    async def get_by_email(cls, email: str):
        return await cls.user.get_or_none(email=email)

    @classmethod
    async def create(
        cls, payload: schemas.UserPayload, is_admin: bool = False
    ) -> tuple[models.User, bool]:
        """
        :param payload: Sign up payload
        :return: None
        """
        if is_admin:
            if not (role := await RoleCRUD.get_by_desc("admin")):
                raise Exception("Unable to find role with description `admin`")
        else:
            if not (role := await RoleCRUD.get_by_desc("user")):
                raise Exception("Unable to find role with description `role`")

        dump = payload.model_dump()

        dump["password_hash"] = auth.hash_password(dump.pop("password"))
        dump["is_active"] = True
        dump["role_id"] = role.id
        email = dump.pop("email")

        return await cls.user.get_or_create(dump, email=email)


class RoleCRUD:
    role = models.Role

    @classmethod
    async def get_all(cls):
        return await cls.role.all()

    @classmethod
    async def get_by_desc(cls, desc: str) -> models.Role | None:
        return await cls.role.get_or_none(description=desc)

    @classmethod
    async def create(cls, payload: schemas.RolePayload) -> tuple[models.Role, bool]:
        dump = payload.model_dump()
        desc = dump.pop("description")

        return await cls.role.get_or_create(dump, description=desc)

    @classmethod
    async def elevate_role(cls, email: str) -> bool:
        if not (user := await UserCRUD.get_by_email(email)):
            return False

        if not (admin_role := await RoleCRUD.get_by_desc("admin")):
            return False

        user.role_id = admin_role.id
        await user.save()

        return True
