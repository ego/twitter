"""Base module."""

from abc import ABC, abstractmethod

__all__ = ("DB", "AsyncDB")


class DB(ABC):
    """DB abstract class."""

    @abstractmethod
    def validate_settings(self):
        """Validate settings."""

    @abstractmethod
    def dsn(self):
        """DB DSN."""


class AsyncDB(ABC):
    """Async DB abstract class."""

    @abstractmethod
    def create_engine(self):
        """Create engine."""

    @abstractmethod
    async def startup(self, app):
        """On engine startup."""

    @abstractmethod
    async def cleanup(self, app):
        """On engine cleanup."""
