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