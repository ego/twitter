"""Tests module."""
import logging
import time

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import URL
from sqlalchemy_utils.functions import (
    create_database,
    database_exists,
    drop_database,
)

from web.app import create_app
from web.settings import SettingsTest


@pytest.fixture(scope="session")
def pg_dsn():
    """PG DSN."""
    settings = SettingsTest()
    return str(
        URL(
            database=settings.DB_NAME,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            username=settings.DB_USER,
            drivername=settings.DB_DRIVERNAME,
        )
    )


@pytest.fixture(scope="session")
def pg_engine(pg_dsn):
    """pg_engine fixture for function or session scope."""
    dsn = pg_dsn
    if database_exists(dsn):
        drop_database(dsn)
    create_database(dsn)
    engine = create_engine(dsn)
    # create tables
    with open("/service/sql/init.sql") as fd:
        escaped_sql = text(fd.read())
        logging.debug(escaped_sql)
        engine.execute(escaped_sql)
    # wait for DB
    time.sleep(10)
    # check DB
    engine.execute("""select * from tweets limit 1;""")
    # session
    yield engine
    # ends
    engine.dispose()
    drop_database(dsn)


@pytest.fixture
def test_app(loop, aiohttp_client):
    """App  fixture."""
    app = create_app(test=True)
    return loop.run_until_complete(aiohttp_client(app))
