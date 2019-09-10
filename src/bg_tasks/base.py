"""Abstract base classes for providers like twitter, instagram, etc."""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager

__all__ = ("AsyncAPI", "AsyncConsumer", "AsyncTasks")


class AsyncAPI(ABC):
    """Abstract AsyncAPI."""

    @abstractmethod
    async def create_session(self):
        """Create session."""

    @property
    @abstractmethod
    def session(self):
        """Get session."""

    @asynccontextmanager
    @abstractmethod
    async def rate_limit(self):
        """Hold rate limit."""


class AsyncConsumer(ABC):
    """Abstract AsyncConsumer."""

    @abstractmethod
    async def run_forever(self, app):
        """Run task forever."""


class AsyncTasks(ABC):
    """Abstract AsyncTasks."""

    @abstractmethod
    async def startup_bg_tasks(self, app):
        """On startup tasks."""

    @abstractmethod
    async def cleanup_bg_tasks(self, app):
        """On cleanup tasks."""
