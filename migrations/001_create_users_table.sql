SET timezone = 'UTC';

CREATE TABLE IF NOT EXISTS users (
    id                BIGINT PRIMARY KEY,
    username          VARCHAR(32),
    first_name        VARCHAR(64) NOT NULL DEFAULT '',
    last_name         VARCHAR(64),
    language_code     VARCHAR(10) DEFAULT 'en',
    is_premium        BOOLEAN NOT NULL DEFAULT FALSE,
    is_banned         BOOLEAN NOT NULL DEFAULT FALSE,
    ban_reason        TEXT,
    ban_until         TIMESTAMPTZ,
    count_downloads   INTEGER NOT NULL DEFAULT 0,
    count_audio       INTEGER NOT NULL DEFAULT 0,
    count_images      INTEGER NOT NULL DEFAULT 0,
    count_playlists   INTEGER NOT NULL DEFAULT 0,
    preferred_codec   VARCHAR(10) DEFAULT 'avc1',
    preferred_mkv     BOOLEAN DEFAULT FALSE,
    split_size_mb     INTEGER DEFAULT 0,
    subs_enabled      BOOLEAN DEFAULT FALSE,
    subs_language     VARCHAR(10) DEFAULT 'en',
    subs_auto_mode    VARCHAR(20) DEFAULT 'off',
    keyboard_mode     VARCHAR(10) DEFAULT '2x3',
    nsfw_enabled      BOOLEAN DEFAULT FALSE,
    custom_args       JSONB DEFAULT '{}',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS username VARCHAR(32),
    ADD COLUMN IF NOT EXISTS first_name VARCHAR(64) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS last_name VARCHAR(64),
    ADD COLUMN IF NOT EXISTS language_code VARCHAR(10) DEFAULT 'en',
    ADD COLUMN IF NOT EXISTS is_premium BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS is_banned BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS ban_reason TEXT,
    ADD COLUMN IF NOT EXISTS ban_until TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS count_downloads INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS count_audio INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS count_images INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS count_playlists INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS preferred_codec VARCHAR(10) DEFAULT 'avc1',
    ADD COLUMN IF NOT EXISTS preferred_mkv BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS split_size_mb INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS subs_enabled BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS subs_language VARCHAR(10) DEFAULT 'en',
    ADD COLUMN IF NOT EXISTS subs_auto_mode VARCHAR(20) DEFAULT 'off',
    ADD COLUMN IF NOT EXISTS keyboard_mode VARCHAR(10) DEFAULT '2x3',
    ADD COLUMN IF NOT EXISTS nsfw_enabled BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS custom_args JSONB DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS last_activity TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users(last_activity);
CREATE INDEX IF NOT EXISTS idx_users_is_banned ON users(is_banned);
