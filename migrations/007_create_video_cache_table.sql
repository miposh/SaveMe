CREATE TABLE IF NOT EXISTS video_cache (
    id              SERIAL PRIMARY KEY,
    url_hash        VARCHAR(64) NOT NULL,
    quality         VARCHAR(20) NOT NULL,
    telegram_file_id TEXT NOT NULL,
    telegram_msg_ids INTEGER[],
    title           TEXT,
    duration_sec    INTEGER,
    file_size_bytes BIGINT,
    is_playlist     BOOLEAN DEFAULT FALSE,
    playlist_url    TEXT,
    playlist_index  INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(url_hash, quality)
);

ALTER TABLE video_cache
    ADD COLUMN IF NOT EXISTS url_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS quality VARCHAR(20),
    ADD COLUMN IF NOT EXISTS telegram_file_id TEXT,
    ADD COLUMN IF NOT EXISTS telegram_msg_ids INTEGER[],
    ADD COLUMN IF NOT EXISTS title TEXT,
    ADD COLUMN IF NOT EXISTS duration_sec INTEGER,
    ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT,
    ADD COLUMN IF NOT EXISTS is_playlist BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS playlist_url TEXT,
    ADD COLUMN IF NOT EXISTS playlist_index INTEGER,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_video_cache_url_hash ON video_cache(url_hash);
CREATE INDEX IF NOT EXISTS idx_video_cache_playlist ON video_cache(is_playlist, playlist_url);
