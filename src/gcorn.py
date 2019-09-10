"""Gunicorn module.

gunicorn gcorn:app --bind localhost:8888
    --worker-class aiohttp.GunicornWebWorker

or aiohttp.GunicornUVLoopWebWorker
"""

import asyncio

from main import application_factory

loop = asyncio.get_event_loop()
app = loop.run_until_complete(application_factory())
