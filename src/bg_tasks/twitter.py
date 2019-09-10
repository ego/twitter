"""Twitter provider."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Union

import aiohttp
from aiohttp.web_app import Application

from bg_tasks.base import AsyncAPI, AsyncConsumer, AsyncTasks
from db.pg.models import Query, Tweets
from web.settings import Settings

__all__ = ("AsyncTwitterAPI", "AsyncTwitterConsumer", "AsyncTwitterTasks")


class AsyncTwitterAPI(AsyncAPI):
    """Twitter API."""

    api_url: str = "https://api.twitter.com"
    token_url: str = f"{api_url}/oauth2/token"
    tweets_url: str = f"{api_url}/1.1/search/tweets.json"

    def __init__(self, settings: Settings) -> None:
        """Make async twitter API."""
        self._access_token: str
        self._session: aiohttp.ClientSession
        self._auth_headers: dict
        self._last_request_time: float = 0
        self._basic_auth = aiohttp.BasicAuth(
            settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET
        )
        self._query_phrase: str = settings.TWITTER_QUERY_PHRASE
        self._last_tweets_count: int = settings.TWITTER_LAST_TWEETS_COUNT
        self._task_period: int = settings.TWITTER_TASK_PERIOD

    async def create_session(self) -> None:
        """Initialize session."""
        await self.token()
        self._auth_headers = {"Authorization": f"Bearer {self._access_token}"}
        self._session = aiohttp.ClientSession(headers=self._auth_headers)

    @property
    def session(self) -> aiohttp.ClientSession:
        """Return valid session with token."""
        assert self._session
        return self._session

    @asynccontextmanager
    async def rate_limit(self) -> AsyncGenerator[None, None]:
        """Twetter API limits requests - 15-min window (user auth) = 180.

        It is 1 req per 5 sec.
        """
        if time.time() - self._last_request_time < 300:  # it is 5 sec
            await asyncio.sleep(5)
        self._last_request_time = time.time()
        yield

    async def token(self) -> None:
        """Get token from twitter API."""
        params: dict = {"grant_type": "client_credentials"}
        headers: dict = {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }
        async with aiohttp.ClientSession(
            headers=headers, auth=self._basic_auth
        ) as session:
            async with self.rate_limit():
                async with session.post(self.token_url, params=params) as resp:
                    res = await resp.json()
                    self._access_token = res["access_token"]

    async def search_tweets(self) -> AsyncGenerator[Any, Union[Dict, None]]:
        """Scroll back (in past) for `self._last_tweets_count` tweets."""
        count: int = min([self._last_tweets_count, 100])
        tweets_count: int = 0
        params: Union[Dict, None] = {"q": self._query_phrase, "count": count}
        url: str = self.tweets_url
        while tweets_count <= self._last_tweets_count:
            async with self.rate_limit():
                async with self.session.get(url, params=params) as resp:
                    json_data = await resp.json()
                    tweets_count += len(json_data["statuses"])
                    yield json_data["statuses"]

                    params = None
                    next_results: str = json_data["search_metadata"].get(
                        "next_results"
                    )
                    if not next_results:
                        break
                    url = self.tweets_url + next_results


class AsyncTwitterConsumer(AsyncConsumer, AsyncTwitterAPI):
    """Asynchronous twitter consumer."""

    async def run_forever(self, app: Application) -> None:
        """Create new row in query table with query phrase.

        Setup twitter session with token, and loop forever.
        It get last `self._last_tweets_count` tweets queried
        by specific phrase once in a configured period of time
        `self._task_period` with rate limits `self.rate_limit`
        and save tweets into DB.
        """
        try:
            logging.debug("AsyncTwitterConsumer is running now ...")
            query_id = await Query.save(app["pg"], self._query_phrase)
            await self.create_session()
            while True:
                async for tweets in self.search_tweets():
                    if tweets:
                        await Tweets.save(app["pg"], query_id, tweets)
                await asyncio.sleep(self._task_period)
        except asyncio.CancelledError as e:
            logging.error(e)
        finally:
            if self.session:
                await self.session.close()
            logging.debug("AsyncTwitterConsumer is stoped.")


class AsyncTwitterTasks(AsyncTasks, AsyncTwitterConsumer):
    """Run asynchronous twitter tasks."""

    async def startup_bg_tasks(self, app: Application) -> None:
        """Create new asyncio task with twitter consumer."""
        app["twitter_session"] = app.loop.create_task(self.run_forever(app))

    async def cleanup_bg_tasks(self, app: Application) -> None:
        """Cancel asyncio task."""
        app["twitter_session"].cancel()
        await app["twitter_session"]
