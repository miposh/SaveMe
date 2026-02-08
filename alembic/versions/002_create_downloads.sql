CREATE TABLE IF NOT EXISTS downloads (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_url TEXT NOT NULL,
    video_title TEXT NOT NULL,
    download_type VARCHAR(20) NOT NULL,
    quality VARCHAR(20),
    file_size BIGINT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_downloads_user_id ON downloads (user_id);
CREATE INDEX IF NOT EXISTS idx_downloads_created_at ON downloads (created_at DESC);
