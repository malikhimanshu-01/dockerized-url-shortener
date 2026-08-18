-- Schema for the url-shortener project (section 5 of PLAN.md).
-- Executed automatically by the official Postgres image on first container init
-- (anything in /docker-entrypoint-initdb.d runs once, against an empty data directory).

CREATE TABLE IF NOT EXISTS links (
    id          SERIAL PRIMARY KEY,
    short_code  VARCHAR(16) NOT NULL UNIQUE,
    long_url    TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at  TIMESTAMPTZ NULL,
    owner_id    INTEGER NULL
);

CREATE TABLE IF NOT EXISTS clicks (
    id          SERIAL PRIMARY KEY,
    link_id     INTEGER NOT NULL REFERENCES links(id) ON DELETE CASCADE,
    clicked_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    referrer    TEXT NULL,
    user_agent  TEXT NULL,
    country     VARCHAR(2) NULL
);

CREATE INDEX IF NOT EXISTS idx_clicks_link_id ON clicks (link_id);
