CREATE TABLE IF NOT EXISTS broadcasts (
    id                SERIAL PRIMARY KEY,
    admin_id          BIGINT NOT NULL,
    text              TEXT NOT NULL,
    media_file_id     TEXT,
    media_type        VARCHAR(20),
    url_buttons       TEXT,
    segment           VARCHAR(20) NOT NULL DEFAULT 'all',
    scheduled_at      TIMESTAMPTZ,
    status            VARCHAR(20) NOT NULL DEFAULT 'draft',
    is_ab_test        BOOLEAN NOT NULL DEFAULT FALSE,
    ab_variant        VARCHAR(1),
    ab_parent_id      INTEGER REFERENCES broadcasts(id) ON DELETE CASCADE,
    total_recipients  INTEGER NOT NULL DEFAULT 0,
    sent_count        INTEGER NOT NULL DEFAULT 0,
    failed_count      INTEGER NOT NULL DEFAULT 0,
    blocked_count     INTEGER NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_broadcasts_status ON broadcasts(status);
CREATE INDEX IF NOT EXISTS idx_broadcasts_scheduled_at ON broadcasts(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_broadcasts_admin_id ON broadcasts(admin_id);
