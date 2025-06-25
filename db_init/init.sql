CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Vocabulary learning tables

CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS phrases (
    id SERIAL PRIMARY KEY,
    original TEXT NOT NULL,
    translation TEXT NOT NULL,
    difficulty INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS phrase_topics (
    phrase_id INTEGER NOT NULL REFERENCES phrases(id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    PRIMARY KEY (phrase_id, topic_id)
);

CREATE VIEW IF NOT EXISTS phrase_view AS
SELECT id, original, translation, difficulty
FROM phrases
ORDER BY difficulty ASC;

CREATE TABLE IF NOT EXISTS progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    phrase_id INTEGER NOT NULL REFERENCES phrases(id) ON DELETE CASCADE,
    answered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    correct BOOLEAN NOT NULL
);
