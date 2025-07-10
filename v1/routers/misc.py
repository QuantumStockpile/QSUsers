from fastapi import APIRouter

from v1.settings import settings, logger

__tags__ = ["misc"]
__prefix__ = ""

router = APIRouter()


@router.get("/api-info")
async def get_api_info():
    return dict(
        api_version=settings.api.version, build_version=settings.api.build_version
    )
