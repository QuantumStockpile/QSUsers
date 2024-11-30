from . import schemas, models, auth


class UserCRUD:
    user = models.User

    @classmethod
    async def get_all(cls):
        return await cls.user.all()

    @classmethod
    async def get_by_email(cls, email: str):
        return await cls.user.get(email=email)

    @classmethod
    async def create(cls, payload: schemas.UserPayload) -> tuple[models.User, bool]:
        """
        :param payload: Sign up payload
        :return: None
        """
        dump = payload.model_dump()

        p_hash = auth.hash_password(dump.pop("password"))

        return await cls.user.get_or_create(**dump, password_hash=p_hash, is_active=True)
