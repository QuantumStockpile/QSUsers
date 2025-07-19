import datetime as dt
from datetime import datetime, timedelta
from typing import Dict, List

import jwt
from fastapi.security import OAuth2PasswordBearer
import bcrypt

from v1.settings import settings
from .role_scopes import RoleScopes

SECRET_KEY, ALGORITHM = settings.security.secret_key, settings.security.algorithm

# Extended scopes for equipment management system
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        # User scopes
        "users:me": "Read information about the current user",
        "users:read": "Read users",
        "users:create": "Create users",
        # Equipment scopes
        "equipment:read": "Read equipment catalog",
        "equipment:create": "Add equipment to catalog",
        "equipment:update": "Update equipment information",
        "equipment:delete": "Delete equipment",
        # Request/Borrow scopes
        "requests:create": "Create borrow requests",
        "requests:read": "Read borrow requests",
        "requests:update": "Update request status",
        "requests:approve": "Approve/deny requests",
        # Reports scopes
        "reports:read": "Generate and read reports",
        "reports:export": "Export reports and borrowing history",
        # Admin scopes
        "admin:full": "Full administrative access",
        "roles:manage": "Manage user roles",
    },
)

# Initialize role hierarchy and generate role scopes
_role_scopes = RoleScopes()
ROLE_SCOPES: Dict[str, List[str]] = _role_scopes.build_all_role_scopes()


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode("utf-8")


def verify_password(password: str, hash: str) -> bool:
    password_enc = password.encode("utf-8")
    hash_enc = hash.encode("utf-8")
    return bcrypt.checkpw(password_enc, hash_enc)


def get_scopes_for_role(role_name: str) -> List[str]:
    """Get all scopes for a given role using the role hierarchy"""
    try:
        return _role_scopes.get_role_scopes(role_name)
    except ValueError:
        # Fallback for unknown roles
        return []


def create_access_token(
    data: dict, expires_delta: timedelta | None = None, scopes: List[str] | None = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(dt.UTC) + (
        expires_delta if expires_delta else timedelta(minutes=60 * 60)
    )

    # Add scopes to token if provided
    if scopes:
        to_encode["scopes"] = scopes

    to_encode.update({"exp": expire, "token_type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(email: str, expires_delta: timedelta | None = None) -> str:
    to_encode: dict[str, str | datetime] = {"sub": email, "token_type": "refresh"}
    expire = datetime.now(dt.UTC) + (
        expires_delta
        if expires_delta
        else timedelta(days=settings.security.refresh_token_expire_days)
    )
    to_encode["exp"] = expire

    return jwt.encode(
        to_encode, settings.security.refresh_secret_key, algorithm=ALGORITHM
    )
