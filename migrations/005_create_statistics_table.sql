CREATE TABLE IF NOT EXISTS statistics (
    id              SERIAL PRIMARY KEY,
    user_id         BIGINT,
    event_type      VARCHAR(50) NOT NULL,
    url             TEXT,
    domain          VARCHAR(255),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_statistics_event_type ON statistics(event_type);
CREATE INDEX IF NOT EXISTS idx_statistics_created_at ON statistics(created_at);
CREATE INDEX IF NOT EXISTS idx_statistics_user_id ON statistics(user_id);
