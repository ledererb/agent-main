CREATE TABLE triage_rules (
    id BIGSERIAL PRIMARY KEY,
    situation TEXT NOT NULL,
    priority TEXT NOT NULL,
    escalation_email TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
