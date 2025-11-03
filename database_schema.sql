-- filepath: database_schema.sql
-- commit_message: Initial database schema for reviews and suspicious entities

CREATE TABLE reviews (
    review_id VARCHAR(255) PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    reviewer_id VARCHAR(255) NOT NULL,
    review_text TEXT,
    review_rating INTEGER,
    review_date TIMESTAMP WITH TIME ZONE NOT NULL,
    reviewer_ip VARCHAR(45), -- Supports IPv4 and IPv6
    is_flagged BOOLEAN DEFAULT FALSE,
    flag_reasons TEXT[] DEFAULT ARRAY[]::TEXT[], -- Array of strings
    manual_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'abusive', 'legitimate'
    flagged_at TIMESTAMP WITH TIME ZONE,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add indices for frequent query fields
CREATE INDEX idx_reviews_reviewer_id ON reviews (reviewer_id);
CREATE INDEX idx_reviews_is_flagged ON reviews (is_flagged);
CREATE INDEX idx_reviews_manual_status ON reviews (manual_status);
CREATE INDEX idx_reviews_review_date ON reviews (review_date);
CREATE INDEX idx_reviews_reviewer_ip ON reviews (reviewer_ip);

CREATE TABLE suspicious_entities (
    entity_id VARCHAR(255) PRIMARY KEY,
    entity_type VARCHAR(10) NOT NULL, -- 'ip' or 'user'
    reason TEXT,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Table to store ingestion state
CREATE TABLE ingestion_metadata (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) UNIQUE NOT NULL,
    last_successful_run TIMESTAMP WITH TIME ZONE
);

INSERT INTO ingestion_metadata (service_name, last_successful_run) VALUES ('amazon_review_ingestion', NULL);