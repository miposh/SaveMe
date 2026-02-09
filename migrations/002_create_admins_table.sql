CREATE TABLE IF NOT EXISTS admins (
    id          BIGINT PRIMARY KEY,
    username    VARCHAR(32),
    added_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    added_by    BIGINT
);

CREATE INDEX IF NOT EXISTS idx_admins_added_at ON admins(added_at);
