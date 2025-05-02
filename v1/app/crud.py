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
    async def create(cls, payload: schemas.UserPayload) -> tuple[models.User, bool]:
        """
        :param payload: Sign up payload
        :return: None
        """
        dump = payload.model_dump()

        dump["password_hash"] = auth.hash_password(dump.pop("password"))
        dump["is_active"] = True
        email = dump.pop("email")

        return await cls.user.get_or_create(dump, email=email)
