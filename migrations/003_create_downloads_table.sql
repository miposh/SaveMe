CREATE TABLE IF NOT EXISTS downloads (
    id              SERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url             TEXT NOT NULL,
    url_hash        VARCHAR(64) NOT NULL,
    domain          VARCHAR(255),
    title           TEXT,
    duration_sec    INTEGER,
    file_size_bytes BIGINT,
    quality         VARCHAR(20),
    media_type      VARCHAR(20) DEFAULT 'video',
    telegram_file_id TEXT,
    telegram_msg_id  INTEGER,
    tags            JSONB DEFAULT '[]',
    is_nsfw         BOOLEAN DEFAULT FALSE,
    is_playlist     BOOLEAN DEFAULT FALSE,
    playlist_index  INTEGER,
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE downloads
    ADD COLUMN IF NOT EXISTS user_id BIGINT,
    ADD COLUMN IF NOT EXISTS url TEXT,
    ADD COLUMN IF NOT EXISTS url_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS domain VARCHAR(255),
    ADD COLUMN IF NOT EXISTS title TEXT,
    ADD COLUMN IF NOT EXISTS duration_sec INTEGER,
    ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT,
    ADD COLUMN IF NOT EXISTS quality VARCHAR(20),
    ADD COLUMN IF NOT EXISTS media_type VARCHAR(20) DEFAULT 'video',
    ADD COLUMN IF NOT EXISTS telegram_file_id TEXT,
    ADD COLUMN IF NOT EXISTS telegram_msg_id INTEGER,
    ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS is_nsfw BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS is_playlist BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS playlist_index INTEGER,
    ADD COLUMN IF NOT EXISTS error TEXT,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_downloads_user_id ON downloads(user_id);
CREATE INDEX IF NOT EXISTS idx_downloads_url_hash ON downloads(url_hash);
CREATE INDEX IF NOT EXISTS idx_downloads_domain ON downloads(domain);
CREATE INDEX IF NOT EXISTS idx_downloads_created_at ON downloads(created_at);
CREATE INDEX IF NOT EXISTS idx_downloads_media_type ON downloads(media_type);
