"""Engine module."""

from dataclasses import dataclass
from typing import Any

from aiohttp import web
from aiopg.sa import create_engine
from sqlalchemy.engine.url import URL

from db.base import DB, AsyncDB
from web.settings import Settings

__all__ = ("PG", "AsyncPG")


class PG(DB):
    """PostgreSQL driver."""

    def __init__(self, *args, **kwargs):
        """PG init."""
        super().__init__(*args, **kwargs)
        self.settings = None
        self.validate_settings()

    def validate_settings(self) -> None:
        """Validate DB settings."""
        if self.settings.DB_DRIVERNAME != "postgres":
            raise ValueError("Incorrect driver!")

    @property
    def dsn(self) -> str:
        """DSN url suitable for sqlalchemy and aiopg."""
        return str(
            URL(
                database=self.settings.DB_NAME,
                password=self.settings.DB_PASSWORD,
                host=self.settings.DB_HOST,
                port=self.settings.DB_PORT,
                username=self.settings.DB_USER,
                drivername=self.settings.DB_DRIVERNAME,
            )
        )


@dataclass
class AsyncPG(AsyncDB, PG):
    """Aiopg PostgreSQL driver for aiohttp application."""

    __slots__ = ("settings", "loop")

    settings: Settings
    loop: Any

    def create_engine(self):
        """Create new aiopg engine."""
        return create_engine(self.dsn, loop=self.loop)

    async def startup(self, app: web.Application) -> None:
        """Add aiopg engine on application startup."""
        app["pg"] = await self.create_engine()

    async def cleanup(self, app: web.Application) -> None:
        """Drop aiopg engine on application cleanup."""
        app["pg"].close()
        await app["pg"].wait_closed()
