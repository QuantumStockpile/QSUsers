class RoleScopes:
    """Alternative approach using explicit role inheritance. Holy vibecode"""

    BASE_ROLES = {
        "student": [
            "users:me",
            "equipment:read",
            "requests:create",
            "requests:read",
        ],
    }

    ROLE_INHERITANCE = {
        "teacher": {
            "inherits_from": ["student"],
            "additional_scopes": [],
            "excluded_scopes": [],
        },
        "manager": {
            "inherits_from": ["student"],
            "additional_scopes": [
                "equipment:create",
                "equipment:update",
                "equipment:delete",
                "requests:approve",
                "reports:read",
            ],
            # Optional: exclude specific scopes from inherited roles
            "excluded_scopes": [],
        },
        "admin": {
            "inherits_from": ["student"],
            "additional_scopes": [
                "users:read",
                "users:create",
                "requests:update",
                "requests:approve",
                "reports:read",
                "reports:export",
                "roles:manage",
            ],
            # Example: admin can't directly manage equipment (business rule)
            "excluded_scopes": [],
        },
        "superadmin": {
            "inherits_from": ["admin", "manager"],
            "additional_scopes": [
                "admin:full",
            ],
            "excluded_scopes": [],
        },
        # Example of a restricted role
        "readonly_admin": {
            "inherits_from": ["admin"],
            "additional_scopes": [],
            # Exclude all write operations
            "excluded_scopes": [
                "users:create",
                "requests:update",
                "requests:approve",
                "roles:manage",
            ],
        },
        # Example of a manager without delete permissions
        "junior_manager": {
            "inherits_from": ["manager"],
            "additional_scopes": [],
            "excluded_scopes": [
                "equipment:delete",
            ],
        },
    }

    @classmethod
    def get_role_scopes(cls, role: str) -> list[str]:
        """Get all scopes for a role including inherited ones, minus excluded scopes."""
        if role in cls.BASE_ROLES:
            return cls.BASE_ROLES[role].copy()

        if role not in cls.ROLE_INHERITANCE:
            raise ValueError(f"Unknown role: {role}")

        role_config = cls.ROLE_INHERITANCE[role]
        scopes = set()

        # Add inherited scopes
        for parent_role in role_config["inherits_from"]:
            scopes.update(cls.get_role_scopes(parent_role))

        # Add additional scopes
        scopes.update(role_config["additional_scopes"])

        # Remove excluded scopes
        excluded_scopes = set(role_config.get("excluded_scopes", []))
        scopes -= excluded_scopes

        return sorted(list(scopes))

    @classmethod
    def build_all_role_scopes(cls) -> dict[str, list[str]]:
        """Build complete role scopes mapping with exclusions applied."""
        all_roles = set(cls.BASE_ROLES.keys())
        all_roles.update(cls.ROLE_INHERITANCE.keys())

        return {role: cls.get_role_scopes(role) for role in all_roles}

    @classmethod
    def get_excluded_scopes(cls, role: str) -> list[str]:
        """Get the scopes that are explicitly excluded for a role."""
        if role in cls.BASE_ROLES:
            return []

        if role not in cls.ROLE_INHERITANCE:
            raise ValueError(f"Unknown role: {role}")

        return cls.ROLE_INHERITANCE[role].get("excluded_scopes", [])

    @classmethod
    def get_inherited_scopes(cls, role: str) -> dict[str, list[str]]:
        """Get scopes broken down by where they come from (inheritance vs direct)."""
        if role in cls.BASE_ROLES:
            return {
                "direct": cls.BASE_ROLES[role].copy(),
                "inherited": [],
                "excluded": [],
            }

        if role not in cls.ROLE_INHERITANCE:
            raise ValueError(f"Unknown role: {role}")

        role_config = cls.ROLE_INHERITANCE[role]
        inherited_scopes = set()

        # Collect inherited scopes
        for parent_role in role_config["inherits_from"]:
            inherited_scopes.update(cls.get_role_scopes(parent_role))

        direct_scopes = set(role_config["additional_scopes"])
        excluded_scopes = set(role_config.get("excluded_scopes", []))

        return {
            "direct": sorted(list(direct_scopes)),
            "inherited": sorted(list(inherited_scopes - direct_scopes)),
            "excluded": sorted(list(excluded_scopes)),
        }

    @classmethod
    def validate_exclusions(cls) -> list[str]:
        """Validate that excluded scopes actually exist in inherited roles."""
        issues = []

        for role, config in cls.ROLE_INHERITANCE.items():
            excluded_scopes = set(config.get("excluded_scopes", []))
            if not excluded_scopes:
                continue

            # Get all scopes that would be available without exclusions
            available_scopes = set()
            for parent_role in config["inherits_from"]:
                available_scopes.update(cls.get_role_scopes(parent_role))
            available_scopes.update(config["additional_scopes"])

            # Check if excluded scopes are actually available to exclude
            invalid_exclusions = excluded_scopes - available_scopes
            if invalid_exclusions:
                issues.append(
                    f"Role '{role}' tries to exclude scopes that aren't available: "
                    f"{sorted(list(invalid_exclusions))}"
                )

        return issues

    @classmethod
    def create_role_with_exclusions(
        cls,
        role_name: str,
        inherits_from: list[str],
        additional_scopes: list[str] | None = None,
        excluded_scopes: list[str] | None = None,
    ) -> None:
        """Dynamically create a new role with exclusions."""
        cls.ROLE_INHERITANCE[role_name] = {
            "inherits_from": inherits_from,
            "additional_scopes": additional_scopes or [],
            "excluded_scopes": excluded_scopes or [],
        }

    @classmethod
    def add_scope_exclusion(cls, role: str, scope: str) -> bool:
        """Add a scope exclusion to an existing role."""
        if role not in cls.ROLE_INHERITANCE:
            return False

        excluded_scopes = cls.ROLE_INHERITANCE[role].get("excluded_scopes", [])
        if scope not in excluded_scopes:
            excluded_scopes.append(scope)
            cls.ROLE_INHERITANCE[role]["excluded_scopes"] = excluded_scopes

        return True

    @classmethod
    def remove_scope_exclusion(cls, role: str, scope: str) -> bool:
        """Remove a scope exclusion from an existing role."""
        if role not in cls.ROLE_INHERITANCE:
            return False

        excluded_scopes = cls.ROLE_INHERITANCE[role].get("excluded_scopes", [])
        if scope in excluded_scopes:
            excluded_scopes.remove(scope)

        return True

    @classmethod
    def get_role_analysis(cls, role: str) -> dict:
        """Get comprehensive analysis of a role's permissions."""
        try:
            scope_breakdown = cls.get_inherited_scopes(role)
            final_scopes = cls.get_role_scopes(role)

            return {
                "role": role,
                "total_scopes": len(final_scopes),
                "final_scopes": final_scopes,
                "direct_scopes": scope_breakdown["direct"],
                "inherited_scopes": scope_breakdown["inherited"],
                "excluded_scopes": scope_breakdown["excluded"],
                "scope_sources": cls._get_scope_sources(role),
            }
        except ValueError as e:
            return {"error": str(e)}

    @classmethod
    def _get_scope_sources(cls, role: str) -> dict[str, list[str]]:
        """Get which parent roles contribute which scopes."""
        if role in cls.BASE_ROLES:
            return {role: cls.BASE_ROLES[role]}

        if role not in cls.ROLE_INHERITANCE:
            return {}

        sources = {}
        role_config = cls.ROLE_INHERITANCE[role]

        # Add direct scopes
        if role_config["additional_scopes"]:
            sources[role] = role_config["additional_scopes"]

        # Add inherited scopes
        for parent_role in role_config["inherits_from"]:
            parent_scopes = cls.get_role_scopes(parent_role)
            if parent_scopes:
                sources[parent_role] = parent_scopes

        return sources
