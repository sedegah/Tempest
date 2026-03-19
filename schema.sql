DROP TABLE IF EXISTS access_logs;
DROP TABLE IF EXISTS shared_files;

CREATE TABLE shared_files (
    id TEXT PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    original_name TEXT NOT NULL,
    uploaded_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    max_downloads INTEGER DEFAULT 1,
    download_count INTEGER DEFAULT 0,
    encryption_key TEXT,
    password TEXT
);

CREATE TABLE IF NOT EXISTS short_links (
    id TEXT PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    shared_file_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    max_downloads INTEGER DEFAULT 1,
    download_count INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (shared_file_id) REFERENCES shared_files (id)
);

CREATE TABLE IF NOT EXISTS access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shared_file_id TEXT NOT NULL,
    accessed_at DATETIME NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    status TEXT NOT NULL,
    FOREIGN KEY (shared_file_id) REFERENCES shared_files(id) ON DELETE CASCADE
);
