"""Models module."""

from typing import Any, Dict, List, Union

import sqlalchemy as sa
from aiopg.sa.engine import Engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import text
from sqlalchemy.sql.selectable import Select

__all__ = ("Query", "Tweets")


SABase: Any = declarative_base()


class Base(SABase):
    """Abstract `sqlalchemy` class for models."""

    __abstract__ = True

    @classmethod
    def upsert(cls, values: Union[Dict, List[Dict]]) -> postgresql.dml.Insert:
        """Generate SQL upsert with `do nothing` for model `cls.__table__`."""
        return (
            postgresql.insert(cls.__table__)
            .values(values)
            .on_conflict_do_nothing()
        )


class Query(Base):
    """Query table for storing query phrase.

    Sharing it with other tables by `id` field.
    Index field `phrase` for read performance.
    """

    __tablename__ = "query"

    id = sa.Column(  # noqa
        sa.BigInteger, primary_key=True, nullable=False, autoincrement=True
    )
    published_at = sa.Column(sa.Date, nullable=False)
    phrase = sa.Column(sa.Text, nullable=False)

    @classmethod
    def get_by_phrasee(cls, phrase: str) -> Select:
        """Generate SQL for getting `Query` row by phrase, ignore register."""
        return cls.__table__.select().where(
            sa.func.lower(cls.__table__.c.phrase) == sa.func.lower(phrase)
        )

    @classmethod
    async def save(cls, pg: Engine, query: str) -> int:
        """Upsert by unique `phrase` row into table `query`.

        Return it's `id`. Upsert `on_conflict_do_nothing`
        do not return `id`, so we need fetch it.
        """
        async with pg.acquire() as conn:
            async for row in conn.execute(cls.upsert({"phrase": query})):
                if row:
                    return row[0]
            async for row in conn.execute(cls.get_by_phrasee(query)):
                return row[0]
        assert row
        return row[0]


class Tweets(Base):
    """Tweets table for storing all incoming unique tweets."""

    __tablename__ = "tweets"

    id = sa.Column(  # noqa
        sa.BigInteger, primary_key=True, nullable=False, autoincrement=True
    )
    api_id = sa.Column(sa.Text, nullable=False)
    published_at = sa.Column(sa.DateTime, nullable=False)
    phrase = sa.Column(sa.Text, nullable=False)
    hashtags = sa.Column(sa.ARRAY(sa.Text))
    author_id = sa.Column(sa.BigInteger, nullable=False)
    query_id = sa.Column(sa.BigInteger, nullable=False)

    @classmethod
    async def save(cls, pg: Engine, query_id: int, tweets: List[Dict]) -> None:
        """On save tweet call SQL `tweets_trigger`.

        And upsert `hashtags` and `authors` tables rows.
        More info in `sql/init.sql` file.
        """
        rows = []
        for tweet in tweets:
            hashtags = [tag["text"] for tag in tweet["entities"]["hashtags"]]
            row = {
                "api_id": tweet["id"],
                "published_at": tweet["created_at"],
                "phrase": tweet["text"],
                "hashtags": hashtags or None,
                "author_id": tweet["user"]["id"],
                "query_id": query_id,
            }
            rows.append(row)
        async with pg.acquire() as conn:
            await conn.execute(cls.upsert(rows))

    @classmethod
    async def unique_tweets(
        cls, pg: Engine, phrase: str, count: int, offset: int = 0
    ):
        """Return unique tweets by phrase with limit/offset."""
        rows = []
        count = min([count, 100])
        query = text(
            """
            SELECT to_jsonb(t) FROM tweets t JOIN query q ON t.query_id = q.id
                WHERE lower(q.phrase) = lower(:phrase)
                ORDER BY t.published_at desc LIMIT :count OFFSET :offset
            """
        )
        async with pg.acquire() as conn:
            async for row in conn.execute(
                query, dict(phrase=phrase, count=count, offset=offset)
            ):
                rows.append(row[0])
        return rows

    @classmethod
    async def count_tweets(
        cls, pg: Engine, phrase: str, from_date: str, to_date: str
    ):
        """Count of tweets for given phrase and from_date/to_date."""
        rows = []
        query = text(
            """
            SELECT json_build_object('counter', count(t.id)) as data
                FROM tweets t JOIN query q ON t.query_id = q.id
                WHERE lower(q.phrase) = lower(:phrase)
                    AND t.published_at >= date(:from_date)
                    AND t.published_at <= date(:to_date)
            """
        )
        async with pg.acquire() as conn:
            async for row in conn.execute(
                query,
                dict(phrase=phrase, from_date=from_date, to_date=to_date),
            ):
                rows.append(row[0])
        return rows


class Hashtags:
    """Query for hashtags table."""

    @classmethod
    async def top(
        cls,
        pg: Engine,
        phrase: str,
        from_date: str,
        to_date: str,
        top_count: int = 3,
    ):
        """Top Hashtags."""
        rows = []
        query = text(
            """
            SELECT json_build_object('tag', h.tag, 'counter', sum(h.counter))
             as data FROM hashtags h JOIN query q ON h.query_id = q.id
                WHERE lower(q.phrase) = lower(:phrase)
                    AND h.published_at >= date(:from_date)
                    AND h.published_at <= date(:to_date)
                GROUP BY h.tag
                ORDER BY sum(h.counter) DESC
                LIMIT :top_count
            """
        )
        async with pg.acquire() as conn:
            async for row in conn.execute(
                query,
                dict(
                    phrase=phrase,
                    from_date=from_date,
                    to_date=to_date,
                    top_count=top_count,
                ),
            ):
                rows.append(row[0])
        return rows


class Authors:
    """Query for authors table."""

    @classmethod
    async def top(
        cls,
        pg: Engine,
        phrase: str,
        from_date: str,
        to_date: str,
        top_count: int = 3,
    ):
        """Top Authors."""
        rows = []
        query = text(
            """
            SELECT json_build_object(
                'author_id', a.author_id,
                'counter', sum(a.counter)) as data
                FROM authors a JOIN query q ON a.query_id = q.id
                WHERE lower(q.phrase) = lower(:phrase)
                    AND a.published_at >= date(:from_date)
                    AND a.published_at <= date(:to_date)
                GROUP BY a.author_id
                ORDER BY sum(a.counter) DESC
                LIMIT :top_count
            """
        )
        async with pg.acquire() as conn:
            async for row in conn.execute(
                query,
                dict(
                    phrase=phrase,
                    from_date=from_date,
                    to_date=to_date,
                    top_count=top_count,
                ),
            ):
                rows.append(row[0])
        return rows
