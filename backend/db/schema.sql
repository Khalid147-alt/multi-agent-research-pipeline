CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS sessions (
    id          UUID PRIMARY KEY,
    topic       TEXT NOT NULL,
    status      VARCHAR(20) DEFAULT 'running',
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reports (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID UNIQUE REFERENCES sessions(id),
    topic       TEXT NOT NULL,
    content     TEXT,
    pdf_path    TEXT,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    id          BIGSERIAL PRIMARY KEY,
    session_id  UUID REFERENCES sessions(id),
    event_type  VARCHAR(50),
    agent_name  VARCHAR(100),
    payload     JSONB,
    created_at  TIMESTAMP DEFAULT NOW()
);
