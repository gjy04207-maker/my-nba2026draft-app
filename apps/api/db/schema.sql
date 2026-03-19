-- Core entities
CREATE TABLE IF NOT EXISTS teams (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  abbreviation TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS players (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  team_id INTEGER REFERENCES teams(id),
  position TEXT,
  status TEXT
);

CREATE TABLE IF NOT EXISTS games (
  id SERIAL PRIMARY KEY,
  game_date DATE NOT NULL,
  home_team_id INTEGER REFERENCES teams(id),
  away_team_id INTEGER REFERENCES teams(id),
  status TEXT,
  source TEXT
);

-- Stats snapshots
CREATE TABLE IF NOT EXISTS team_stats (
  id SERIAL PRIMARY KEY,
  team_id INTEGER REFERENCES teams(id),
  season TEXT,
  metric TEXT NOT NULL,
  value NUMERIC,
  source TEXT,
  fetched_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS player_stats (
  id SERIAL PRIMARY KEY,
  player_id INTEGER REFERENCES players(id),
  season TEXT,
  metric TEXT NOT NULL,
  value NUMERIC,
  source TEXT,
  fetched_at TIMESTAMP NOT NULL
);

-- News items
CREATE TABLE IF NOT EXISTS news_items (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  url TEXT,
  source TEXT,
  published_at TIMESTAMP,
  fetched_at TIMESTAMP NOT NULL,
  summary TEXT
);

-- CBA rules index (text + metadata)
CREATE TABLE IF NOT EXISTS cba_rules (
  id SERIAL PRIMARY KEY,
  page INTEGER NOT NULL,
  paragraph INTEGER NOT NULL,
  text TEXT NOT NULL,
  source_pdf TEXT
);

-- User style samples (your historical reviews)
CREATE TABLE IF NOT EXISTS style_samples (
  id SERIAL PRIMARY KEY,
  title TEXT,
  content TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL
);

-- Embeddings (pgvector required)
-- CREATE EXTENSION IF NOT EXISTS vector;
-- ALTER TABLE cba_rules ADD COLUMN embedding vector(1536);
-- ALTER TABLE style_samples ADD COLUMN embedding vector(1536);
