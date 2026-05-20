CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    topic       TEXT NOT NULL,
    status      TEXT DEFAULT 'running',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reports (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    session_id  TEXT UNIQUE REFERENCES sessions(id),
    topic       TEXT NOT NULL,
    content     TEXT,
    pdf_path    TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT REFERENCES sessions(id),
    event_type  TEXT,
    agent_name  TEXT,
    payload     TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);
