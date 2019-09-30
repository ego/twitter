CREATE TABLE query (
    id               serial PRIMARY KEY NOT NULL,
    published_at     timestamp NOT NULL DEFAULT NOW(),
    phrase           text NOT NULL UNIQUE
);
CREATE INDEX idx_query_phrase on query (lower(phrase));

-- Best of all keep this table without indexes for write performance.
-- In future we can split tables into read and write tables with syncing job for them.
CREATE TABLE tweets (
    id               serial PRIMARY KEY NOT NULL,
    api_id           text NOT NULL UNIQUE,    -- from twitter hold only unique
    published_at     timestamp not null,
    phrase           text not null,
    hashtags         text[],                  -- as array
    author_id        bigint not null,
    query_id         bigint NOT NULL REFERENCES query (id)  -- task query phrase
);

-- For improvement aggregating statistic for each queried phrase we will
-- store unique (day, query_id, tag) hashtags per day (using partitions feature)
-- and summarise it's counters directly.
CREATE TABLE hashtags (
    published_at     date NOT NULL,
    query_id         bigint NOT NULL REFERENCES query (id),
    tag              text not null,
    counter          bigint default 1
) PARTITION BY RANGE (published_at);
CREATE UNIQUE INDEX idx_unique_hashtags on hashtags (published_at, query_id, lower(tag));

-- Do same and for authors statistic.
CREATE TABLE authors (
    published_at     date NOT NULL,
    query_id         bigint NOT NULL REFERENCES query (id),
    author_id        bigint NOT NULL,
    counter          bigint DEFAULT 1
) PARTITION BY RANGE (published_at);
CREATE UNIQUE INDEX idx_unique_authors on authors (published_at, query_id, author_id);

-- Function for creating partitions, you can run it when you will need more partition.
-- We do not create partitions automatically because it will increase cost for insertion time,
-- so do it manually or in applications logic by some periodic task.
CREATE OR REPLACE FUNCTION create_partitions(table_name text, statistic_day date) RETURNS VOID AS
$BODY$
DECLARE
    sql text;
BEGIN
 select format('CREATE TABLE %s_%s PARTITION OF %s
  FOR VALUES FROM (''%s'') TO (''%s'')', table_name, (replace(statistic_day::text, '-', '_')), table_name, statistic_day, (statistic_day + INTERVAL '1 DAY')::date) into sql;
 EXECUTE sql;
END;
$BODY$
LANGUAGE plpgsql;

-- Create partitions for table hashtags from 10 DAY in past to 1 YEAR in future over over each day.
SELECT create_partitions('hashtags', statistic_day::date) FROM generate_series
  (current_date - INTERVAL '10 DAY', current_date + INTERVAL '1 YEAR', '1 DAY'::interval) statistic_day;

-- Create partitions for table authors from 10 DAY in past to 1 YEAR in future over over each day.
SELECT create_partitions('authors', statistic_day::date) FROM generate_series
  (current_date - INTERVAL '10 DAY', current_date + INTERVAL '1 YEAR', '1 DAY'::interval) statistic_day;

-- Triggers for hashtags and authors
CREATE OR REPLACE FUNCTION tweets_trigger() RETURNS trigger AS $tweets_trigger$
    DECLARE
    tag_item text;
    BEGIN
        IF NEW.hashtags IS NOT NULL THEN
             FOREACH tag_item IN ARRAY NEW.hashtags LOOP
                INSERT INTO hashtags (published_at, query_id, tag)
                  VALUES (NEW.published_at::date, NEW.query_id, tag_item)
                  ON CONFLICT (published_at, query_id, lower(tag))
                  DO UPDATE SET counter = hashtags.counter + 1;
             END LOOP;
        END IF;
        INSERT INTO authors (published_at, query_id, author_id)
          VALUES (NEW.published_at::date, NEW.query_id, NEW.author_id)
          ON CONFLICT (published_at, query_id, author_id)
          DO UPDATE SET counter = authors.counter + 1;
        RETURN NEW;
    END;
$tweets_trigger$ LANGUAGE plpgsql;

-- Insert hashtags and authors only when we save unique tweets
-- to avoid duplication caunters for statistic.
CREATE TRIGGER tweets_trigger AFTER INSERT OR UPDATE ON tweets
    FOR EACH ROW EXECUTE FUNCTION tweets_trigger();
