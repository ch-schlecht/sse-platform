CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(200) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    hashed_password VARCHAR,
    role VARCHAR(100),
    google_user BOOLEAN
);

CREATE TABLE IF NOT EXISTS password_reset (
    phrase VARCHAR(200) PRIMARY KEY,
    email VARCHAR(200) NOT NULL UNIQUE
);
