"""API module."""

from datetime import datetime

from aiohttp import web

from db.pg.models import Authors, Hashtags, Tweets


async def tweets(request):
    """Tweets.

    :param request: Context injected by aiohttp framework
    :type request: RequestHandler

    ---
    description:
        Return last `settings.TWITTER_LAST_TWEETS_COUNT` tweets.
        Max size is `100` tweets, for more items use `offset` query param.
    tags:
    - All unique tweets
    produces:
    - application/json
    parameters:
    - in: path
      name: offset
      required: false
      type: integer
    responses:
        "200":
            description: successful operation.
        "400":
            description: incorrect operation.
    """
    try:
        offset = int(request.match_info.get("offset") or 0)
    except Exception:  # noqa pylint: disable=broad-except
        return web.Response(text="Incorrect offset!", status=400)

    settings = request.app["settings"]
    res = await Tweets.unique_tweets(
        request.app["pg"],
        settings.TWITTER_QUERY_PHRASE,
        settings.TWITTER_LAST_TWEETS_COUNT,
        offset,
    )
    return web.json_response(res)


def validate_date(request):
    """Validate dates params."""
    from_date = request.match_info.get("from_date")
    to_date = request.match_info.get("to_date")

    try:
        datetime.fromisoformat(from_date).date()
        datetime.fromisoformat(to_date).date()
    except Exception:  # noqa pylint: disable=broad-except
        return None, None
    return from_date, to_date


async def top_hashtags(request):
    """Top hashtags.

    :param request: Context injected by aiohttp framework
    :type request: RequestHandler

    ---
    description:
        Return TOP 3 `hashtags` with `counter` for given date range
        `from_date` and `to_date`.
    tags:
    - Top hashtags
    produces:
    - application/json
    parameters:
    - in: path
      name: from_date
      required: true
      type: string
      description: example 2019-09-09
    - in: path
      name: to_date
      required: true
      type: string
      description: example 2019-09-10
    responses:
        "200":
            description: successful operation.
        "400":
            description: incorrect operation.
    """
    from_date, to_date = validate_date(request)
    if not from_date:
        return web.Response(text="Incorrect dates!", status=400)

    settings = request.app["settings"]
    res = await Hashtags.top(
        request.app["pg"], settings.TWITTER_QUERY_PHRASE, from_date, to_date
    )
    return web.json_response(res)


async def top_authors(request):
    """Top authors.

    :param request: Context injected by aiohttp framework
    :type request: RequestHandler

    ---
    description:
        Return TOP 3 `authors` with `counter` for given date range
        `from_date` and `to_date`.
    tags:
    - Top authors
    produces:
    - application/json
    parameters:
    - in: path
      name: from_date
      required: true
      type: string
      description: example 2019-09-09
    - in: path
      name: to_date
      required: true
      type: string
      description: example 2019-09-10
    responses:
        "200":
            description: successful operation.
        "400":
            description: incorrect operation.
    """
    from_date, to_date = validate_date(request)
    if not from_date:
        return web.Response(text="Incorrect dates!", status=400)

    settings = request.app["settings"]
    res = await Authors.top(
        request.app["pg"], settings.TWITTER_QUERY_PHRASE, from_date, to_date
    )
    return web.json_response(res)


async def count_tweets(request):
    """Count tweets.

    :param request: Context injected by aiohttp framework
    :type request: RequestHandler

    ---
    description:
        Return `counter` of `tweets` for given date range
        `from_date` and `to_date`.
    tags:
    - Count tweets
    produces:
    - application/json
    parameters:
    - in: path
      name: from_date
      required: true
      type: string
      description: example 2019-09-09
    - in: path
      name: to_date
      required: true
      type: string
      description: example 2019-09-10
    responses:
        "200":
            description: successful operation.
        "400":
            description: incorrect operation.
    """
    from_date, to_date = validate_date(request)
    if not from_date:
        return web.Response(text="Incorrect dates!", status=400)

    settings = request.app["settings"]
    res = await Tweets.count_tweets(
        request.app["pg"], settings.TWITTER_QUERY_PHRASE, from_date, to_date
    )
    return web.json_response(res)
