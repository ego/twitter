"""Application entry point.

For production it will be better run application under `Nginx`
and `gunicorn` with fast `uvloop`.
"""

from aiohttp.web import Application

from web.app import create_app


async def application_factory() -> Application:
    """Production application factory."""
    app = create_app()
    return app


def adev() -> Application:
    """Develop application factory."""
    app = create_app()
    return app
