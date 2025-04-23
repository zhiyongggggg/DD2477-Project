CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS books_read (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    title TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE search_history (
    id SERIAL PRIMARY KEY,               
    user_id INTEGER NOT NULL,            
    query TEXT NOT NULL,                 
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
);
