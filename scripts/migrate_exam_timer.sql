-- Для существующей БД (create_all не меняет старые таблицы)
ALTER TABLE attempts ADD COLUMN IF NOT EXISTS mode VARCHAR(20) NOT NULL DEFAULT 'training';
CREATE INDEX IF NOT EXISTS ix_attempts_mode ON attempts (mode);

CREATE TABLE IF NOT EXISTS ticket_attempts (
    id SERIAL PRIMARY KEY,
    attempt_id INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    timed_out BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_attempt_ticket UNIQUE (attempt_id, ticket_id)
);
CREATE INDEX IF NOT EXISTS ix_ticket_attempts_attempt_id ON ticket_attempts (attempt_id);
CREATE INDEX IF NOT EXISTS ix_ticket_attempts_ticket_id ON ticket_attempts (ticket_id);
