-- Database Schema for Amazon Review Abuse Detection System

-- Table for storing raw and processed Amazon product reviews
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    review_id VARCHAR(255) UNIQUE NOT NULL, -- Unique identifier from Amazon
    product_id VARCHAR(255) NOT NULL,       -- Amazon Standard Identification Number (ASIN)
    asin VARCHAR(255),
    reviewer_id VARCHAR(255) NOT NULL,
    reviewer_name VARCHAR(255),
    review_title TEXT,
    review_text TEXT NOT NULL,
    overall_rating INTEGER,                 -- 1-5 stars
    review_date TIMESTAMP WITH TIME ZONE NOT NULL,
    purchase_type VARCHAR(50),              -- e.g., 'Verified Purchase'
    ip_address VARCHAR(45),                 -- IP address of the reviewer (IPv4 or IPv6)
    ingestion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Status and flagging fields
    status VARCHAR(50) DEFAULT 'raw',       -- 'raw', 'processed', 'flagged', 'abusive', 'not_abusive', 'needs_investigation'
    is_flagged BOOLEAN DEFAULT FALSE,       -- True if system has flagged it for any reason
    flagged_reason TEXT,                    -- Concatenated reasons for flagging (e.g., "Bad Actor IP Match
Keyword Match")
    flagged_by TEXT,                        -- Comma-separated sources (e.g., "BAD_ACTOR_DETECTION,KEYWORD_DETECTION")
    flagged_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Analyst action fields
    analyst_action_by VARCHAR(100),         -- Username of the analyst who took action
    analyst_action_timestamp TIMESTAMP WITH TIME ZONE
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews (product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_reviewer_id ON reviews (reviewer_id);
CREATE INDEX IF NOT EXISTS idx_reviews_review_date ON reviews (review_date DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_is_flagged_status ON reviews (is_flagged, status);
CREATE INDEX IF NOT EXISTS idx_reviews_flagged_timestamp ON reviews (flagged_timestamp DESC);


-- Table for storing known bad actor identifiers
CREATE TABLE IF NOT EXISTS known_bad_actors (
    id SERIAL PRIMARY KEY,
    actor_type VARCHAR(50) NOT NULL,        -- e.g., 'IP_ADDRESS', 'REVIEWER_ID', 'ACCOUNT_ID'
    actor_value VARCHAR(255) UNIQUE NOT NULL, -- The actual IP, ID, etc.
    reason TEXT,                            -- Why this actor is considered bad
    added_by VARCHAR(100),
    added_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(50) DEFAULT 'HIGH',    -- 'HIGH', 'MEDIUM', 'LOW'
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_kba_actor_value ON known_bad_actors (actor_value);
CREATE INDEX IF NOT EXISTS idx_kba_actor_type_value ON known_bad_actors (actor_type, actor_value);


-- Table for storing abuse-related keywords and phrases
CREATE TABLE IF NOT EXISTS abuse_keywords (
    id SERIAL PRIMARY KEY,
    keyword TEXT UNIQUE NOT NULL,           -- The keyword or phrase (e.g., "free product")
    category VARCHAR(100),                  -- e.g., 'INCENTIVIZED', 'FAKE_REVIEW', 'SPAM'
    severity VARCHAR(50) DEFAULT 'MEDIUM',  -- 'HIGH', 'MEDIUM', 'LOW'
    added_by VARCHAR(100),
    added_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE          -- Whether the keyword is currently active for detection
);

-- Table for storing analyst user accounts
CREATE TABLE IF NOT EXISTS analyst_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,    -- Hashed password using bcrypt
    email VARCHAR(255),
    role VARCHAR(50) DEFAULT 'ANALYST',     -- e.g., 'ANALYST', 'ADMIN'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Example: Insert a default analyst user (password: "password123")
INSERT INTO analyst_users (username, password_hash, email) VALUES
('analyst1', '$2b$12$R.Sj.YqN.z5.g.R.Sj.YqN.z5.g.R.Sj.YqN.z5.g.R.Sj.YqN.z5.g.12345678901234567890', 'analyst1@example.com')
ON CONFLICT (username) DO NOTHING; -- Replace with a proper bcrypt hash in production


-- Table for auditing all detection events and analyst actions
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,       -- e.g., 'REVIEW_FLAGGED', 'REVIEW_CLASSIFIED'
    review_id VARCHAR(255) NOT NULL,        -- Link to the review in question
    entity_id VARCHAR(255),                 -- ID of the entity that triggered/was acted upon (e.g., bad actor ID, keyword)
    source VARCHAR(100),                    -- e.g., 'BAD_ACTOR_DETECTION_SERVICE', 'ANALYST_UI'
    details JSONB,                          -- Flexible JSON field for additional event-specific details
    performed_by VARCHAR(100),              -- User or service account that performed the action
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_review_id ON audit_log (review_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_event_type ON audit_log (event_type);
