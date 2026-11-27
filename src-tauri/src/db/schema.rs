
pub const SCHEMA: &str = r#"
CREATE TABLE IF NOT EXISTS topics(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at INTEGER NOT NULL DEFAULT (unixepoch()),
    is_active INTEGER NOT NULL DEFAULT 1
);
"#;