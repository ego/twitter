"""Global settings for application.

Map ENV vars to python settings class.
"""

import logging
import os
from dataclasses import dataclass

__all__ = ("Settings",)


@dataclass
class Settings:
    """Application settings."""

    LOGGING_LEVEL: int = int(os.environ.get("LOGGING_LEVEL") or logging.DEBUG)
    DB_DRIVERNAME: str = "postgres"
    DB_USER: str = os.environ["POSTGRES_USER"]
    DB_PASSWORD: str = os.environ["POSTGRES_PASSWORD"]
    DB_NAME: str = os.environ["POSTGRES_DB"]
    DB_HOST: str = "pg"
    DB_PORT: int = 5432

    TWITTER_CONSUMER_KEY: str = os.environ["TWITTER_CONSUMER_KEY"]
    TWITTER_CONSUMER_SECRET: str = os.environ["TWITTER_CONSUMER_SECRET"]
    TWITTER_QUERY_PHRASE: str = os.environ["TWITTER_QUERY_PHRASE"]
    TWITTER_LAST_TWEETS_COUNT: int = int(
        os.environ["TWITTER_LAST_TWEETS_COUNT"]
    )
    TWITTER_TASK_PERIOD: int = int(os.environ["TWITTER_TASK_PERIOD"])


@dataclass
class SettingsTest(Settings):
    """Test settings."""

    LOGGING_LEVEL: int = logging.DEBUG
    DB_NAME: str = os.environ["POSTGRES_TEST_DB"]
    TWITTER_QUERY_PHRASE: str = "cote"
