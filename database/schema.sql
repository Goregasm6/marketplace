CREATE TABLE IF NOT EXISTS listings (

id INTEGER PRIMARY KEY AUTOINCREMENT,

source TEXT,

title TEXT,

description TEXT,

price REAL,

url TEXT,

location TEXT,

category TEXT,

date_found DATETIME,

flip_score INTEGER DEFAULT 0,

estimated_value REAL DEFAULT 0,

status TEXT DEFAULT 'new'

);

CREATE TABLE IF NOT EXISTS queues (

id TEXT PRIMARY KEY,

opportunity_id TEXT NOT NULL UNIQUE,

status TEXT NOT NULL DEFAULT 'new',

review_notes TEXT,

reviewed_at DATETIME,

created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP

);
