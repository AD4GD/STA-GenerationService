from fastapi import Request

from src.settings import settings


def router_root():
    def root(request: Request):
        if settings.DEBUG:
            response = {
                "value": [{"name": name, "url": f"{request.url}{name}"} for name in settings.API_RESOURCES_NAMES]
            }
        else:
            response = {
                "value": [
                    {"name": name, "url": f"{request.url}{name}".replace(settings.HTTP, settings.HTTPS)}
                    for name in settings.API_RESOURCES_NAMES
                ]
            }

        return response

    return root
