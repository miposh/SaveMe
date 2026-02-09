SET timezone = 'UTC';

ALTER TABLE IF EXISTS users
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

ALTER TABLE IF EXISTS admins
    ADD COLUMN IF NOT EXISTS username VARCHAR(32),
    ADD COLUMN IF NOT EXISTS added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS added_by BIGINT;

ALTER TABLE IF EXISTS downloads
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
    ADD COLUMN IF NOT EXISTS video_url TEXT,
    ADD COLUMN IF NOT EXISTS audio_url TEXT,
    ADD COLUMN IF NOT EXISTS image_url TEXT,
    ADD COLUMN IF NOT EXISTS video_title TEXT,
    ADD COLUMN IF NOT EXISTS download_type VARCHAR(20),
    ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS error_message TEXT,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'downloads'
          AND column_name = 'video_url'
    ) THEN
        EXECUTE 'ALTER TABLE downloads ALTER COLUMN video_url DROP NOT NULL';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'downloads'
          AND column_name = 'audio_url'
    ) THEN
        EXECUTE 'ALTER TABLE downloads ALTER COLUMN audio_url DROP NOT NULL';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'downloads'
          AND column_name = 'image_url'
    ) THEN
        EXECUTE 'ALTER TABLE downloads ALTER COLUMN image_url DROP NOT NULL';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'downloads'
          AND column_name = 'video_title'
    ) THEN
        EXECUTE 'ALTER TABLE downloads ALTER COLUMN video_title DROP NOT NULL';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'downloads'
          AND column_name = 'download_type'
    ) THEN
        EXECUTE 'ALTER TABLE downloads ALTER COLUMN download_type DROP NOT NULL';
    END IF;
END $$;

ALTER TABLE IF EXISTS rate_limits
    ADD COLUMN IF NOT EXISTS user_id BIGINT,
    ADD COLUMN IF NOT EXISTS period VARCHAR(10),
    ADD COLUMN IF NOT EXISTS request_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS window_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS cooldown_until TIMESTAMPTZ;

ALTER TABLE IF EXISTS statistics
    ADD COLUMN IF NOT EXISTS user_id BIGINT,
    ADD COLUMN IF NOT EXISTS event_type VARCHAR(50),
    ADD COLUMN IF NOT EXISTS url TEXT,
    ADD COLUMN IF NOT EXISTS domain VARCHAR(255),
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

ALTER TABLE IF EXISTS broadcasts
    ADD COLUMN IF NOT EXISTS admin_id BIGINT,
    ADD COLUMN IF NOT EXISTS text TEXT,
    ADD COLUMN IF NOT EXISTS media_file_id TEXT,
    ADD COLUMN IF NOT EXISTS media_type VARCHAR(20),
    ADD COLUMN IF NOT EXISTS url_buttons TEXT,
    ADD COLUMN IF NOT EXISTS segment VARCHAR(20) DEFAULT 'all',
    ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'draft',
    ADD COLUMN IF NOT EXISTS is_ab_test BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS ab_variant VARCHAR(1),
    ADD COLUMN IF NOT EXISTS ab_parent_id INTEGER,
    ADD COLUMN IF NOT EXISTS total_recipients INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS sent_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS failed_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS blocked_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

ALTER TABLE IF EXISTS video_cache
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

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users(last_activity);
CREATE INDEX IF NOT EXISTS idx_users_is_banned ON users(is_banned);

CREATE INDEX IF NOT EXISTS idx_admins_added_at ON admins(added_at);

CREATE INDEX IF NOT EXISTS idx_downloads_user_id ON downloads(user_id);
CREATE INDEX IF NOT EXISTS idx_downloads_url_hash ON downloads(url_hash);
CREATE INDEX IF NOT EXISTS idx_downloads_domain ON downloads(domain);
CREATE INDEX IF NOT EXISTS idx_downloads_created_at ON downloads(created_at);
CREATE INDEX IF NOT EXISTS idx_downloads_media_type ON downloads(media_type);

CREATE UNIQUE INDEX IF NOT EXISTS idx_rate_limits_user_period_unique ON rate_limits(user_id, period);
CREATE INDEX IF NOT EXISTS idx_rate_limits_user_period ON rate_limits(user_id, period);

CREATE INDEX IF NOT EXISTS idx_statistics_event_type ON statistics(event_type);
CREATE INDEX IF NOT EXISTS idx_statistics_created_at ON statistics(created_at);
CREATE INDEX IF NOT EXISTS idx_statistics_user_id ON statistics(user_id);

CREATE INDEX IF NOT EXISTS idx_broadcasts_status ON broadcasts(status);
CREATE INDEX IF NOT EXISTS idx_broadcasts_scheduled_at ON broadcasts(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_broadcasts_admin_id ON broadcasts(admin_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_video_cache_url_hash_quality_unique ON video_cache(url_hash, quality);
CREATE INDEX IF NOT EXISTS idx_video_cache_url_hash ON video_cache(url_hash);
CREATE INDEX IF NOT EXISTS idx_video_cache_playlist ON video_cache(is_playlist, playlist_url);
