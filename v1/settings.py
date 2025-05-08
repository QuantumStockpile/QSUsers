from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

ENVS_PATH = Path("env")

__all__ = ["settings"]


class _SecuritySettings(BaseSettings):
    access_token_expire_minutes: int
    secret_key: str
    algorithm: str


# noinspection PyUnboundLocalVariable
class _APISettings(BaseSettings):
    title: str
    version: str | Path = Path("v1")
    build_version: str
    version_path: Path | None = Path(version)


class _Settings(BaseSettings):
    security: _SecuritySettings
    api: _APISettings


_security_settings = _SecuritySettings(_env_file=ENVS_PATH / "security.env")  # type: ignore
_api_settings = _APISettings(_env_file=ENVS_PATH / "api.env")  # type: ignore

settings = _Settings(security=_security_settings, api=_api_settings)
