from . import schemas, models, auth


class UserCRUD:
    user = models.User

    @classmethod
    async def get_all(cls):
        return await cls.user.all().prefetch_related("roles")

    @classmethod
    async def get_by_email(cls, email: str):
        return await cls.user.get_or_none(email=email).prefetch_related("roles")

    @classmethod
    async def get_by_id(cls, user_id: int):
        return await cls.user.get_or_none(id=user_id).prefetch_related("roles")

    @classmethod
    async def create(
        cls, payload: schemas.UserPayload, is_admin: bool = False
    ) -> tuple[models.User, bool]:
        """
        :param payload: Sign up payload
        :param is_admin: Whether to assign admin role
        :return: (User instance, created boolean)
        """
        # Determine role to assign
        if is_admin:
            if not (role := await RoleCRUD.get_by_name("superadmin")):
                raise Exception("Unable to find role with name `superadmin`")
        else:
            if not (role := await RoleCRUD.get_by_name("user")):
                raise Exception("Unable to find role with name `user`")

        dump = payload.model_dump()
        dump["password_hash"] = auth.hash_password(dump.pop("password"))
        dump["is_active"] = True

        # Remove role-related fields from dump since we'll handle roles separately
        email = dump["email"]

        # Create or get user
        user, created = await cls.user.get_or_create(defaults=dump, email=email)

        # Assign role if user was created or doesn't have this role
        if created or not await user.roles.filter(id=role.id).exists():
            await user.roles.add(role)

        return user, created

    @classmethod
    async def add_role(cls, user_id: int, role_name: str) -> bool:
        """
        Add a role to a user
        :param user_id: User ID
        :param role_name: Role name to add
        :return: Success boolean
        """
        user = await cls.get_by_id(user_id)
        if not user:
            return False

        role = await RoleCRUD.get_by_name(role_name)
        if not role:
            return False

        # Check if user already has this role
        if await user.roles.filter(id=role.id).exists():
            return True  # Already has role

        await user.roles.add(role)
        return True

    @classmethod
    async def remove_role(cls, user_id: int, role_name: str) -> bool:
        """
        Remove a role from a user
        :param user_id: User ID
        :param role_name: Role name to remove
        :return: Success boolean
        """
        user = await cls.get_by_id(user_id)
        if not user:
            return False

        role = await RoleCRUD.get_by_name(role_name)
        if not role:
            return False

        await user.roles.remove(role)
        return True

    @classmethod
    async def has_role(cls, user_id: int, role_name: str) -> bool:
        """
        Check if user has a specific role
        :param user_id: User ID
        :param role_name: Role name to check
        :return: Boolean indicating if user has role
        """
        user = await cls.get_by_id(user_id)
        if not user:
            return False

        return await user.roles.filter(name=role_name).exists()

    @classmethod
    async def get_user_roles(cls, user_id: int) -> list[models.Role]:
        """
        Get all roles for a user
        :param user_id: User ID
        :return: List of roles
        """
        user = await cls.get_by_id(user_id)
        if not user:
            return []

        return await user.roles.all()


class RoleCRUD:
    role = models.Role

    @classmethod
    async def get_all(cls):
        return await cls.role.all().prefetch_related("users")

    @classmethod
    async def get_by_name(cls, name: str) -> models.Role | None:
        return await cls.role.get_or_none(name=name)

    @classmethod
    async def get_by_id(cls, role_id: int) -> models.Role | None:
        return await cls.role.get_or_none(id=role_id)

    @classmethod
    async def create(cls, payload: schemas.RolePayload) -> tuple[models.Role, bool]:
        dump = payload.model_dump()
        name = dump["name"]

        return await cls.role.get_or_create(defaults=dump, name=name)

    @classmethod
    async def elevate_role(cls, email: str) -> bool:
        """
        Add admin role to user (keeping existing roles)
        :param email: User email
        :return: Success boolean
        """
        user = await UserCRUD.get_by_email(email)
        if not user:
            return False

        admin_role = await cls.get_by_name("admin")
        if not admin_role:
            return False

        # Check if user already has admin role
        if await user.roles.filter(id=admin_role.id).exists():
            return True  # Already an admin

        await user.roles.add(admin_role)
        return True

    @classmethod
    async def demote_admin(cls, email: str) -> bool:
        """
        Remove admin role from user
        :param email: User email
        :return: Success boolean
        """
        user = await UserCRUD.get_by_email(email)
        if not user:
            return False

        admin_role = await cls.get_by_name("admin")
        if not admin_role:
            return False

        await user.roles.remove(admin_role)
        return True

    @classmethod
    async def get_users_with_role(cls, role_name: str) -> list[models.User]:
        """
        Get all users with a specific role
        :param role_name: Role name
        :return: List of users
        """
        role = await cls.get_by_name(role_name)
        if not role:
            return []

        return await role.users.all()

    @classmethod
    async def delete_role(cls, role_name: str) -> bool:
        """
        Delete a role (this will remove it from all users)
        :param role_name: Role name to delete
        :return: Success boolean
        """
        role = await cls.get_by_name(role_name)
        if not role:
            return False

        await role.delete()
        return True
