"""Bse application module."""

import logging

from aiohttp import web
from aiohttp.web import Application
from aiohttp_swagger import setup_swagger

from bg_tasks.twitter import AsyncTwitterTasks
from db.pg.engine import AsyncPG
from web.routes import setup_routes
from web.settings import Settings, SettingsTest

__all__ = ("create_app",)


def create_app(test=False) -> Application:
    """Create instance of application.

    Setup hooks, engine and API routes.
    Start web server and base periodic
    background task `AsyncTwitterTasks`.
    """
    app = web.Application()
    settings = SettingsTest() if test else Settings()
    logging.basicConfig(level=settings.LOGGING_LEVEL)
    app.update(name="Social network", settings=settings)

    pg_engine = AsyncPG(settings, app.loop)
    app.on_startup.append(pg_engine.startup)
    app.on_cleanup.append(pg_engine.cleanup)

    twitter = AsyncTwitterTasks(settings)
    app.on_startup.append(twitter.startup_bg_tasks)
    app.on_cleanup.append(twitter.cleanup_bg_tasks)

    setup_routes(app)
    setup_swagger(app, swagger_url="/api/v1/doc")
    return app
