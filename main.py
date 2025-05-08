import importlib
import os

import uvicorn as uvicorn
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from v1.settings import settings


application = FastAPI(
    title=settings.api.title,
    version=f"{settings.api.version}.{settings.api.build_version}",
    root_path="/v1",
)

TORTOISE_CONFIG = {
    "connections": {"default": os.environ["DATABASE_URL"]},
    "apps": {
        "models": {
            "models": ["v1.app.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}


def configure_tortoise(app: FastAPI):
    """
    Generates a list of paths to the models, includes aerich, then registers Tortoise

    :param app: Instance of FastAPI class
    :return:
    """
    register_tortoise(
        app,
        config=TORTOISE_CONFIG,
        generate_schemas=True,
        add_exception_handlers=True,
    )


def include_routers(app: FastAPI):
    """
    Routers must contain the variables **__tags__** and **__prefix__** \n
    If router's name starts with "_" it won't be included

    :param app: Instance of FastAPI class
    :return: None
    """
    for module_name in os.listdir(settings.api.version_path / "routers"):
        if module_name.startswith("_") or not module_name.endswith(".py"):
            continue

        module = importlib.import_module(
            f"v1.routers.{module_name.removesuffix('.py')}"
        )

        app.include_router(
            module.router, tags=module.__tags__, prefix=module.__prefix__
        )


configure_tortoise(application)
include_routers(application)


# if __name__ == "__main__":
#     uvicorn.run("main:application", host="0.0.0.0", port=8000, reload=True)
