-- SQL Schema Definition for 'bad_actors' table
CREATE TABLE bad_actors (
    id UUID PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL, -- 'ACCOUNT', 'IP', 'DOMAIN'
    entity_value VARCHAR(255) UNIQUE NOT NULL, -- The actual account ID, IP address, or domain
    status VARCHAR(50) NOT NULL, -- 'ACTIVE', 'BLACKLISTED', 'SUSPENDED'
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient lookup
CREATE INDEX idx_bad_actors_entity_value ON bad_actors (entity_value);
CREATE INDEX idx_bad_actors_entity_type ON bad_actors (entity_type);