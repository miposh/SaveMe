CREATE TABLE IF NOT EXISTS rate_limits (
    id              SERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    period          VARCHAR(10) NOT NULL,
    request_count   INTEGER NOT NULL DEFAULT 0,
    window_start    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cooldown_until  TIMESTAMPTZ,
    UNIQUE(user_id, period)
);

CREATE INDEX IF NOT EXISTS idx_rate_limits_user_period ON rate_limits(user_id, period);
