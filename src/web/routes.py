"""Web server routes module."""

from aiohttp.web import Application

from web.api import count_tweets, top_authors, top_hashtags, tweets

API_VERSION = "/api/v1"


def setup_routes(app: Application) -> None:
    """Application API URIS."""
    app.router.add_get(API_VERSION + "/tweets/", tweets, name="tweets")
    app.router.add_get(
        API_VERSION + "/tweets/{offset}/", tweets, name="tweets_offset"
    )
    app.router.add_get(
        API_VERSION + "/statistic/top/hashtags/{from_date}/{to_date}/",
        top_hashtags,
        name="top_hashtags",
    )
    app.router.add_get(
        API_VERSION + "/statistic/top/authors/{from_date}/{to_date}/",
        top_authors,
        name="top_authors",
    )
    app.router.add_get(
        API_VERSION + "/statistic/tweets/{from_date}/{to_date}/",
        count_tweets,
        name="count_tweets",
    )
